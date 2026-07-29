# IRQ Pinning Causing System Freezes — Session Notes

## System
- CPU: Intel Core Ultra 7 265K (P-cores 0-7 @ 5.4 GHz, E-cores 8-19 @ 4.6 GHz)
- GPU: NVIDIA RTX 5060 Ti, driver 595.71.05
- Display: Wayland + KDE Plasma 6.6.5 (KWin 6.6.5)
- Manjaro Linux, kernel 7.0.10-1

## The Script That Broke It

The user had a systemd service (`pin-irqs-dynamic.service`) running at boot that pinned device IRQs to specific CPU cores. The script was written with a well-intentioned but incorrect assumption: that pinning GPU and USB to dedicated E-cores would keep P-cores free for games.

### Original (broken) pinning:

```
NVIDIA GPU IRQs → E-cores 8-9
USB IRQs       → E-cores 10-11
NVMe/Audio/WiFi → E-cores 12-19
P-cores 0-7    → untouched (intended for games)
```

### Why It Failed

- E-cores 8-9 are just 2 threads with 4.6 GHz max and small L2 cache
- A single E-core (core 8) was handling 1.6M+ GPU interrupts
- P-cores 0-7 (5.4 GHz, large L2) sat completely idle for IRQ handling
- When GPU load increased (TF2, Dota 2), the E-core saturated → compositor stalled → full system freeze

### Evidence

IRQ distribution at idle after 30 min uptime:
```
IRQ 146 (nvidia display): 563,360 hits on E-core 8, ZERO on P-cores
IRQ 148 (nvidia other):   1,027,003 hits on E-core 8, ZERO on P-cores
```

IRQ distribution for USB (xhci_hcd) was similarly zero on P-cores.

## The Crash Cascade

```
High GPU load (game/WebGL)
  → GPU generates more interrupts
    → E-core 8 saturated (1.6M+ IRQs/s)
      → KWin can't get GPU interrupt service
        → Desktop freezes (cursor stops, clicks unregistered)
          → Apps time out → dota2 SIGSEGV, Chrome SIGTRAP
            → Filesystem not flushed → orphaned inodes every boot
              → User hits power button → 4 rapid reboots in 90 min
```

### Secondary Effects

- PowerDevil crashing/restarting (unable to register with portal)
- `/home` at 93% full → 7+ orphaned inodes cleared every boot
- EasyEffects + WirePlumber crashed simultaneously (audio stack collapse on Jun 6)
- Chrome had 8 SIGTRAP crashes in 2 minutes on May 31
- dota2 had 5+ SIGSEGV crashes with 670-930 MB core dumps (filling `/home` further)

## C-State Analysis (Arrow Lake Specific)

On Arrow Lake (Core Ultra 200-series), the ACPI cpuidle system exposes only 4 states — there are **no C6/C7** in cpuidle like older Intel CPUs. Deeper hardware C-states are handled internally by Intel PCODE.

### C-state Layout

| State | Name | Wake Latency | Description |
|-------|------|-------------|-------------|
| 0 | POLL | 0 µs | Busy-wait (not real idle) |
| 1 | C1_ACPI | 1 µs | MWAIT halt (wakes instantly) |
| 2 | C2_ACPI | 127 µs | C1E-style enhanced halt |
| 3 | C3_ACPI | **1048 µs** | Deep sleep (package C-state) |

### Impact on IRQ Handling

When a core is in C3 and an interrupt fires, the wake takes **1048 µs**. For a GPU generating 1.6M+ interrupts, even brief dips into C2/C3 between interrupt bursts create cumulative latency that stalls the compositor.

### Disabling C-states on IRQ cores

The simplest approach disables everything deeper than C1 (state index ≥ 2):

```bash
for state_dir in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*; do
    [ -d "$state_dir" ] || continue
    state_num="${state_dir##*state}"  # extract from dir name (state2→2)
    if [ "$state_num" -ge 2 ] 2>/dev/null; then
        echo 1 > "$state_dir"/disable 2>/dev/null
    fi
done
```

⚠️ **Pitfall**: The cpuidle `index` file (`$state_dir/index`) does **not exist** on kernel 7.x (Manjaro/Arch). Reading it returns empty, and the `-ge` check silently fails — no states get disabled. Always extract the index from the directory name using `"${state_dir##*state}"` instead.

This keeps POLL and C1 (≤1 µs wake) and eliminates the 127 µs and 1048 µs penalties.

### P-cores don't need C-state changes

P-cores (0-7) on Arrow Lake run at 5.4 GHz with full L2 cache. Their default C-state handling is sufficient for IRQ response — the hardware wakes them faster from deep sleep than E-cores. C-state management is only needed when pinning IRQs to E-cores.

## The Fixed Script (Two Approaches)

Two templates are available in this skill.

### Approach A — GPU+USB on P-cores (default fix)

Template: `templates/pin-irqs-arrowlake.sh`

```
P-cores 0-1:    GPU IRQs (fast interrupt response)
P-cores 2-3:    USB IRQs (fast input response)
E-cores 12-19:  NVMe, Audio, WiFi, Ethernet (background I/O)
P-cores 4-7:    untouched (free for foreground apps)
```

### Approach B — GPU+USB on E-cores with C-state disable (alternative)

Template: `templates/pin-irqs-arrowlake-ecore.sh`

Some users prefer keeping P-cores completely free for games:

```
E-cores 8-11:   GPU IRQs (4 cores, round-robin — never 1-2)
E-cores 12-13:  USB IRQs (2 cores, separate from GPU, no overlap)
E-cores 14-19:  NVMe, Audio, WiFi, Ethernet (shared, can overlap)
P-cores 0-7:    untouched (free for foreground)
```

Additionally, C2 (127 µs wake) and C3 (1048 µs wake) are disabled on cores 8-13. The EPP is set via cpupower and the performance governor is set explicitly on those cores.

**v4 improvements over v3:**
1. **EPP via cpupower** — `cpupower -c "$cpu" set --epp performance` works around the sysfs lock that occurs when the performance governor is already active
2. **Hex mask for background IRQs** — uses `smp_affinity=fc000` instead of per-IRQ round-robin. The hex mask `0xFC000` covers bits 14-19, allowing the IRQ to land on any of those 6 E-cores
3. **NVMe straggler catch** — post-pinning scan checks if any NVMe IRQs escaped to the GPU/USB zone (bits 8-13 = `0x3F00`) and re-pins them. The NVMe driver sometimes reassigns queue affinity on I/O — this catch detects and reverts that
4. `cpupower` is used instead of direct sysfs writes for EPP, as the performance governor locks the sysfs file

### Installation (either approach):

```bash
sudo cp /usr/local/bin/pin-irqs-dynamic /usr/local/bin/pin-irqs-dynamic.bak
sudo cp <path-to-template> /usr/local/bin/pin-irqs-dynamic
sudo chmod +x /usr/local/bin/pin-irqs-dynamic
sudo systemctl restart pin-irqs-dynamic
```

## Verification

```bash
# Check IRQ distribution
grep "nvidia\|xhci" /proc/interrupts | awk '{printf "IRQ %s → ", $1; for(i=2;i<=21;i++) if($i>0) printf "CPU%d:%d ", i-2, $i; print ""}'

# Check C-states on all cores
for cpu in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19; do
    echo -n "CPU $cpu: "
    for s in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*/disable; do
        name=$(cat $(dirname $s)/name 2>/dev/null)
        dis=$(cat $s 2>/dev/null)
        echo -n "$name=$([ "$dis" = 1 ] && echo DIS || echo ON ) "
    done
    echo
done
```

## Related Symptoms That Point Here

- System freezes completely (not just slow — fully unresponsive)
- Rapid reboots in clusters (3-4 boots in under 2 hours)
- Orphaned inodes cleared at every boot
- Chrome SIGTRAP crashes (internal assertion failures, not segfaults)
- dota2/TF2 SIGSEGV crashes (GPU mem access errors)
- "System not responding" but power LED still on, fans still spinning
