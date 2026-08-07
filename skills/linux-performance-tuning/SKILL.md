---
name: linux-performance-tuning
version: "1.0.0"
description: "Systematic Linux performance auditing and tuning for gaming/workstation hybrid systems — hardware audit, kernel config, IRQ pinning, hybrid CPU scheduling, NVIDIA Wayland optimization, network latency, and context switch investigation."
author: hermes-agent
allowed-tools: Bash, Read, Write, WebSearch
---

# Linux Performance Tuning

Systematic methodology for auditing and tuning Linux systems, especially hybrid CPU architectures (P-cores + E-cores) used for gaming + workstation workloads.

## Triggers

Use this skill when the user asks about any of:
- System performance audit / "find tweaks for my system"
- IRQ pinning or interrupt affinity tuning
- High context switches or input lag
- Scheduler tuning for gaming on hybrid CPUs
- NVIDIA + Wayland performance optimization
- "What configs are making my system slow"
- "Investigate my system for performance issues"
- Terminal feels slow / zsh is laggy / shell sluggish / "commands take a long time to process"
- Alacritty/kitty/foot slow to process input or show prompt
- WiFi performance investigation or wireless network tuning
- Intel BE200/BE202 WiFi card troubleshooting or optimization
- iwlwifi/iwlmld module parameter tuning
- Path MTU discovery on WiFi or capped links
- Wireless latency spikes or throughput below expected
- Network module parameters (iwlwifi, iwlmld, cfg80211) investigation
- Native game input lag / Dota 2 / Source 2 / non-Proton game performance debugging
- Steam Linux Runtime / pressure vessel CPU affinity questions

## Multi-Layer System Audit

Do NOT skip layers. Each layer can reveal issues the others hide.

### Layer 1 — Hardware baseline
```
cat /proc/cpuinfo | grep -m1 "model name"        # CPU
cat /proc/cpuinfo | grep -c "^processor"         # Core count
lspci | grep -i "vga\|3d"                        # GPU
free -h                                          # RAM
lsblk -d -o NAME,SIZE,ROTA,MODEL                 # Disks
uname -a                                         # Kernel version
lsmod | grep nvidia                              # NVIDIA modules
```

### Layer 2 — Boot params and kernel config
```
cat /proc/cmdline                                 # Active kernel params
grep GRUB_CMDLINE_LINUX_DEFAULT /etc/default/grub # Persistent config
cat /sys/devices/system/cpu/intel_pstate/*        # P-state settings
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Layer 3 — Config files audit (check ALL of these)
- `/etc/modprobe.d/*.conf` — module parameters and blacklists
- `/etc/environment` — system-wide env vars
- `~/.config/environment.d/*.conf` — per-service env vars
- `~/.profile` — shell env vars
- `~/.asoundrc` — ALSA config
- `/etc/systemd/system/*.service` — custom systemd units
- `/etc/sysctl.d/*.conf` — kernel tunables
- `/etc/fstab` — mount options
- `/etc/default/grub` — boot params
- `~/.config/kwinrc` — KDE compositor settings

### Layer 4 — Systemd services audit
```
systemctl --failed
systemctl list-timers
systemctl list-units --type=service --state=running
```

### Layer 5 — Environment variable conflicts
Check for DIFFERENT values of the same var across `/etc/environment`, `~/.profile`, `~/.config/environment.d/*.conf`. Common conflicts: `LIBVA_DRIVER_NAME`, `__GL_*`, `KWIN_*`, `DXVK_*`.

### Layer 6 — Memory and VM tuning
```
sysctl vm.swappiness vm.vfs_cache_pressure vm.dirty_ratio vm.dirty_background_ratio
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
cat /proc/sys/vm/watermark_boost_factor
cat /proc/sys/vm/watermark_scale_factor
```

### Layer 7 — Filesystem health
```
sudo tune2fs -l /dev/nvme1n1p1 | grep -E "Filesystem state|Errors"
df -h  # Check for >90% full partitions
```

### Layer 8 — Scheduler analysis

⚠️ **Kernel 7.0+ (EEVDF):** The old CFS tunables (`sched_min_granularity_ns`, `sched_latency_ns`, `sched_wakeup_granularity_ns`) **do not exist** under EEVDF — these paths return `No such file or directory` on kernel 7.0+. EEVDF is the sole scheduler since kernel 6.6, replacing CFS entirely. For 7.0+, check EEVDF debugfs and remaining sysctls:

```
# Kernel 7.0+ (EEVDF) — debugfs tunables (needs root)
sudo cat /sys/kernel/debug/sched/base_slice_ns
sysctl kernel.sched_autogroup_enabled kernel.sched_rt_runtime_us kernel.sched_schedstats
cat /sys/kernel/sched_ext/state 2>/dev/null          # sched_ext active?
cat /sys/kernel/sched_ext/ops 2>/dev/null             # which BPF scheduler?

# Kernel < 6.6 (CFS) — legacy paths (will fail silently on 7.0+)
cat /proc/sys/kernel/sched_min_granularity_ns
cat /proc/sys/kernel/sched_latency_ns
cat /proc/sys/kernel/sched_wakeup_granularity_ns
```
See `references/eevdf-kernel-7.0-transition.md` for migration notes.

## IRQ Pinning for Hybrid CPUs

### Architecture
On Intel hybrid CPUs (Arrow Lake, Raptor Lake, Alder Lake):
- P-cores: highest frequency, larger caches → **reserved for game/foreground**
- E-cores: lower frequency, smaller caches → **all hardware interrupts + background**

### Correct allocation for gaming

```
P-cores:    GAME + foreground apps (zero IRQs, zero interference)
E-core set A: GPU interrupts only
E-core set B: USB interrupts only (separate from GPU)
E-core set C: NVMe, audio, WiFi, ethernet, everything else
```

### Key principle
GPU IRQs and USB IRQs each need **dedicated, non-overlapping** E-cores. The GPU generates 100M+ interrupts per session — if USB shares the same core, mouse/keyboard input gets delayed by GPU IRQ processing.

### Script structure (see references/pin-irqs-dynamic.sh)
```bash
#!/bin/bash
# 1. GPU → E-cores 8-9 (dedicated)
# 2. USB xHCI → E-cores 10-11 (dedicated, no GPU overlap)
# 3. NVMe → E-cores 12-19
# 4. Audio → E-cores 12-19
# 5. WiFi → E-cores 12-19
# 6. Ethernet → E-cores 12-19
```

Each section uses round-robin within its assigned core range. `smp_affinity_list` takes a single CPU number (0-indexed).

### Pitfalls
- **IRQ numbers change between boots** — always grep by driver name, not IRQ number
- `smp_affinity_list` writes fail silently if the process lacks permission — run as root
- Check `cat /proc/interrupts | grep nvidia` after the script runs to verify cores
- `irqbalance` WILL override manual pinning — disable it if using a custom script
- Some NVIDIA IRQ vectors are idle (0 interrupts) — still pin them, the distribution logic handles it
- **NVMe IRQs are managed IRQs** — the NVMe driver may override manual affinity writes for queue completion IRQs (nvme0q1-nvme0q8, nvme1q1-nvme1q8). The write appears to succeed (no error) but the kernel reverts it. This is normal and acceptable since NVMe interrupts are low-rate compared to GPU (hundreds per second vs millions).
- **`isolcpus=domain,managed_irq,0-7` defeats NVMe isolation** — the `managed_irq` flag in `isolcpus` explicitly ALLOWS managed IRQs (MSI-X, such as NVMe queue completions) to target isolated CPUs. Without `managed_irq`, the kernel automatically excludes isolated CPUs from managed IRQ targets. If you see NVMe IO queues landing on isolated CPUs (check via `cat /proc/interrupts | grep nvme`), the fix is to **remove `managed_irq`** from your `isolcpus` parameter — e.g. `isolcpus=domain,0-7` instead of `isolcpus=domain,managed_irq,0-7`. This is a reboot-required change.
- **GPU + USB must NOT overlap** — GPU generates 100M+ interrupts and USB handles mouse/kb input. If they share the same E-core, input latency spikes when GPU IRQ processing delays USB IRQ handling. Dedicate separate E-core ranges.

### Diagnosing IRQ assignments

Before pinning, always verify current IRQ distribution to catch misconfigurations:

```bash
# 1. Check CPU topology
lscpu | grep -E '^CPU\\(s\\)|Core\\(s\\)|Thread'

# 2. Which CPUs are isolated?
cat /sys/devices/system/cpu/isolated

# 3. Overview — who is on which CPU
cat /proc/interrupts | grep -E 'nvidia|nvme|xhci_hcd|iwlwifi|snd_hda|igc'

# 4. Hex-to-CPU quick reference (for 20 CPUs):
#    00001=CPU0  00002=CPU1  00004=CPU2  00008=CPU3
#    00010=CPU4  00020=CPU5  00040=CPU6  00080=CPU7
#    00100=CPU8  00200=CPU9  00400=CPU10 00800=CPU11
#    01000=CPU12 02000=CPU13 04000=CPU14 08000=CPU15
#    10000=CPU16 20000=CPU17 40000=CPU18 80000=CPU19

# 5. Check configured vs actual runtime affinity
#    smp_affinity = what the kernel was told
#    effective_affinity = what's actually happening at runtime
for irq in $(grep "nvme" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  name=$(grep "^ *$irq:" /proc/interrupts | awk '{print $NF}')
  aff=$(cat /proc/irq/$irq/smp_affinity)
  eff=$(cat /proc/irq/$irq/effective_affinity)
  echo "IRQ $irq ($name): configured=$aff effective=$eff"
done

# 6. Classification helper
python3 -c "
data = open('/proc/interrupts').read()
for line in data.splitlines():
    if not any(x in line.lower() for x in ['nvidia','nvme','xhci','iwlwifi','snd_hda','igc']):
        continue
    parts = line.split()
    irq = parts[0].rstrip(':')
    if not irq.isdigit(): continue
    aff = open('/proc/irq/%s/smp_affinity' % irq).read().strip()
    eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    ev = int(eff.replace(',',''), 16)
    ec = [i for i in range(20) if ev & (1<<i)]
    iso = [c for c in ec if c < 8]
    hk = [c for c in ec if c >= 8]
    if iso and not hk: tag = 'ISOLATED ONLY'
    elif iso and hk:   tag = 'SPLIT'
    else:              tag = 'housekeeping'
    print('IRQ %3s aff=%6s eff=%6s CPUs=%-12s %s' % (irq, aff, eff, str(ec), tag))
"
```

See `references/irq-affinity-diagnosis.md` for the hex decoding table and standalone diagnosis script.

## References

- `references/gaming-scheduler-tunables.md` — Scheduler values and context switch investigation (CFS-era; see eevdf for 7.0+)
- `references/eevdf-kernel-7.0-transition.md` — EEVDF migration guide and removed CFS tunables
- `references/sethengine-system-config-june-2026.md` — Full system reference for Arrow Lake 265K + RTX 5060 Ti
- `references/irq-affinity-diagnosis.md` — Hex mask decoding table and standalone IRQ diagnosis commands
- `references/zsh-startup-optimization.md` — Shell startup latency: dead plugin managers, dual theme, async fixes, compdump cleanup
- `references/pin-irqs-dynamic.sh` — Installable script for dynamic IRQ pinning
- `references/wifi-intel-be200-be20x-investigation.md` — Intel BE200/BE202 WiFi 7 investigation: power_scheme CAM, disable_11be, bt_coex, MTU probe methodology, TCP tuning, known ASPM instability background
- `references/complete-parameter-audit.md` — Reusable subagent prompt template for the FULL sysctl+cmdline+CPU parameter audit; enforces a sourced best value (Source URL) per row, not opinion verdicts
- `references/native-game-input-lag-diagnosis.md` — Native Linux game (non-Proton) input lag diagnosis: GPU/CPU utilization imbalance, Dota 2 / Source 2 thread analysis, Steam pressure vessel CPU affinity, launch options, KWin compositor gaming settings, EasyEffects blocklist, full IRQ topology dump per-CPU

### C-state locking for IRQ cores
GPU/USB IRQ cores can enter deep C3 sleep (1048μs wake latency) between interrupts. Lock them to C1 only by disabling C2+.

**Method 1 — cpupower** (simplest):
```bash
cpupower -c 8-11 idle-set -D 2 >/dev/null 2>&1
```
This blocks C2+ sleep. Use `-D 1` for POLL only (0µs).

**Method 2 — sysfs loop** (when cpupower unavailable):
```bash
for cpu in 8 9 10 11 12 13; do
    for state_dir in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*; do
        [ -d "$state_dir" ] || continue
        state_name=$(cat "$state_dir"/name 2>/dev/null)
        state_num="${state_dir##*state}"
        if [ "$state_num" -ge 2 ] 2>/dev/null; then
            echo 1 > "$state_dir"/disable 2>/dev/null
        fi
    done
done
```

**Pitfall — state index file**: The `index` file inside cpuidle state dirs (`$state_dir/index`) does NOT exist on kernel 7.0+ Manjaro. Always use `"${state_dir##*state}"` to extract the number from the directory name (`state2` → `2`).

**Pitfall — EPP ordering**: With `cpufreq.default_governor=performance` active, the `energy_performance_preference` sysfs file is locked and writes fail silently. Use `cpupower` which bypasses this:
```bash
# CORRECT:
cpupower -c "$cpu" set --epp performance >/dev/null 2>&1
echo "performance" > "$cpupath"/cpufreq/scaling_governor 2>/dev/null

# WRONG — fails silently when governor is already performance:
echo "performance" > "$cpupath"/cpufreq/energy_performance_preference 2>/dev/null
```

Add these right before the "Done" line in the pin-irqs script.

### NVMe straggler catch
NVMe drives manage their own MSI-X queue affinity and may override `/proc/irq/` writes. Add a periodic straggler catch that checks hex masks against the GPU/USB zone:

```bash
MASK_14_19="fc000"  # bits 14-19
for irq in $(grep "nvme" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    current_mask=$(cat /proc/irq/$irq/smp_affinity 2>/dev/null)
    if [ -n "$current_mask" ]; then
        dec_mask=$((16#${current_mask}))
        overlap=$((dec_mask & 0x3F00))  # 0x3F00 = bits 8-13 (GPU+USB zone)
        if [ "$overlap" -ne 0 ] 2>/dev/null; then
            echo "$MASK_14_19" > /proc/irq/$irq/smp_affinity 2>/dev/null
        fi
    fi
done
```

This catches stragglers between periodic script runs. The script must be timer-driven (every 5-100min) since the NVMe driver may revert.

### Reference script
See `references/pin-irqs-dynamic.sh` for the full installable script with all sections: NVIDIA→E-cores 8-9, USB→10-11, NVMe/audio/WiFi/ethernet→12-19.

### Session reference
`references/sethengine-system-config-june-2026.md` documents a real Arrow Lake 265K + RTX 5060 Ti + Z890 + Manjaro + KDE Wayland system with all configs, pitfalls, and fixes applied in a live session.

## Scheduler Tuning for Gaming on Hybrid CPUs

### Kernel 7.0+ (EEVDF): CFS tunables do not exist

The CFS scheduler was replaced by EEVDF in kernel 6.6. The old tunables (`sched_min_granularity_ns`, `sched_wakeup_granularity_ns`, `sched_latency_ns`) have no effect and the sysfs paths do not exist. EEVDF auto-tunes task time slices based on virtual deadline — manual tuning is largely unnecessary.

The remaining user-tunable scheduler parameters under EEVDF:
```ini
kernel.sched_autogroup_enabled=0       # Disable terminal session grouping (recommended)
kernel.sched_rt_runtime_us=-1          # Unlimited RT CPU time (required for PipeWire/audio)
kernel.sched_schedstats=0              # Disable scheduler statistics (small overhead reduction)
kernel.sched_util_clamp_min=1024       # Default (max utilization)
```

### `sched_itmt_enabled=1` pitfall — Arrow Lake hybrid CPUs

`sched_itmt_enabled=1` (Intel Turbo Max Technology 3.0 scheduling) is designed for **single-architecture Xeon** CPUs where one core turbos higher than the rest. On hybrid consumer CPUs (Arrow Lake, Raptor Lake, Alder Lake), the kernel's built-in asymmetric CPU capacity awareness (`/sys/devices/system/cpu/cpu*/cpu_capacity`) already handles P-core priority. Having ITMT active on top of native hybrid scheduling causes **double-prioritization** — the kernel skews even harder toward already-preferred P-cores, potentially starving E-cores that need to handle background work and IRQs.

**Check:** `cat /proc/sys/kernel/sched_itmt_enabled` — if `1` and you're on Arrow Lake (Core Ultra 200 series) or Raptor Lake (13th/14th gen), remove `sched_itmt_enabled=1` from GRUB.

**Fix:** Remove `sched_itmt_enabled=1` from `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, run `sudo grub-mkconfig -o /boot/grub/grub.cfg`, reboot. Verify via `cat /proc/sys/kernel/sched_itmt_enabled` → `0`.

### The CFS trap (historical — kernel < 6.6 only)

On pre-EEVDF kernels, `sched_min_granularity_ns=750000` (0.75ms) seemed like "low latency" but hurt gaming:
- At 165fps (6ms/frame): game preempted ~8x per frame
- Each preemption = cache dump + TLB flush + resume overhead
- `sched_wakeup_granularity_ns=1000000` let Chrome steal CPU from the game after just 1ms

On EEVDF (kernel 6.6+), the scheduler handles this natively — the virtual deadline mechanism gives latency-sensitive tasks shorter slices automatically.

### Context switch investigation
When CS seems high:
1. Measure rate: `grep "^ctxt" /proc/stat` over a 3-second interval
2. Find top consumers: check `/proc/*/status` for voluntary + nonvoluntary counts
3. **High voluntary CS**: Normal for Proton/Wine (every Windows API call → 2+ CS via wineserver)
4. **High involuntary CS**: The kernel is forcing the process off CPU — find the source:
   - GPU IRQs on same core (check `cat /proc/interrupts | grep nvidia`)
   - EEVDF preemption (virtual deadline expiration — normal, not tunable on 7.0+)
   - Compare involuntary CS with GPU interrupt count on that core

## Kernel Boot Params (non-isolcpus approaches)

For P-cores free from interrupts WITHOUT isolcpus (which hides cores from the scheduler):

```
# rcu_nocbs — offloads RCU callbacks from P-cores. Works without isolcpus.
# nohz_full — adaptive tickless. PARTIALLY works without isolcpus; timer ticks
#             return when tasks migrate onto the core.
```

`nohz_full` WITHOUT `isolcpus` is **documented as requiring isolcpus** — the kernel will enter adaptive-tick mode when the core has 1 task, but exit it when a second task arrives. On a busy workstation where background tasks (Chrome, Steam) constantly touch P-cores, `nohz_full` without `isolcpus` achieves almost nothing. It's also harmless — the kernel falls back to periodic ticks gracefully.

`rcu_nocbs` OFFLOADS RCU callbacks unconditionally, with or without isolcpus. This provides a small but real benefit — RCU cleanup runs on E-cores instead of P-cores.

**Display refresh rate verification note:**
`kscreen-doctor -o` shows modes with `!` (current) and `*` (preferred) markers. These markers can be misleading on Wayland + NVIDIA — don't assume `!` means the display is actually running at that refresh rate. Verify via KWin's internal state or check Display Settings in System Settings. If VRR is enabled and the monitor seems stuck at 60Hz, the kscreen-doctor output may be reporting the base EDID mode rather than the active VRR rate.

The REAL solution for gaming on a hybrid workstation:
1. Move ALL IRQs to E-cores via pin-irqs script
2. Fix scheduler values to not thrash
3. Use gamemode for priority boost (`renice=-5`, `softrealtime=auto`)
4. Optionally: `taskset -c 0-7 gamemoderun %command%` per-game (no reboot needed)

## NVIDIA + Wayland Performance

### Known issues
- GSP firmware on GB206 (RTX 5060 Ti) IS available (at `/lib/firmware/nvidia/gb206/gsp/`)
- `NVreg_EnableGpuFirmware=1` enables GPU firmware offloading, reducing driver CPU overhead
- NVIDIA IRQ vectors use MSI-X — each new `nvidia` entry in `/proc/interrupts` is a separate vector
- On driver 595+, Wayland with `GBM_BACKEND=nvidia-drm` is the correct backend

### Environment variables (verified working for KDE 6 + NVIDIA 595+)
```
GBM_BACKEND=nvidia-drm
__GLX_VENDOR_LIBRARY_NAME=nvidia
KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1     # KDE6 var (NOT KWIN_TRIPLE_BUFFER which is KDE5)
KWIN_DRM_ALLOW_TEARING=1
__GL_MaxFramesAllowed=1
__GL_SYNC_TO_VBLANK=0
__GL_VRR_ALLOWED=1
```

### GPU Presentation Latency: Intel IOMMU

Intel IOMMU (`intel_iommu=on`) adds DMA address translation to every GPU buffer exchange — every Wayland frame submission, every EGL swap, every texture upload. On a desktop with no VM passthrough (no VFIO), this is pure overhead with no benefit.

**Impact on input latency:** The keyboard-to-display pipeline requires the compositor to present a new frame after every keystroke. Each frame goes through: Alacritty → EGL swap → KWin composition → NVIDIA kernel driver → PCIe DMA. IOMMU wraps every DMA transaction with a translation + permission check. This adds ~0.1-0.5ms per frame.

**Fix:** Remove `intel_iommu=on` from kernel cmdline. The NVIDIA driver talks directly to the GPU via PCIe BAR — it doesn't need IOMMU translation. In fact, on RTX 5000 series (GB206/Blackwell), IOMMU can trigger NVDEC0 GPU MMU faults (NVIDIA Xid 31) because the IOMMU page tables conflict with the GPU's internal VA space manager.

```sh
# GRUB
sudo sed -i 's/ intel_iommu=on,igfx_off//g; s/intel_iommu=on,igfx_off //g; s/intel_iommu=on,igfx_off//g' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg

# systemd-boot
sudo sed -i 's/ intel_iommu=on,igfx_off//g; s/intel_iommu=on,igfx_off//g' /boot/loader/entries/*.conf
```

### Chrome flags that break on NVIDIA Wayland

These flags are known to cause WebGL fallback to SwiftShader (software), slow rendering, GPU context failures, and crashes on NVIDIA Wayland:

| Flag | Effect | Fix |
|------|--------|-----|
| `--use-gl=angle` without `--use-angle=` | ANGLE defaults to SwiftShader on NVIDIA Wayland | Add `--use-angle=vulkan` or use `--use-gl=desktop` |
| `--enable-native-gpu-memory-buffers` | Causes rendering corruption and GPU process crashes | Remove entirely |
| `--enable-features=AcceleratedVideoDecodeLinuxGL` | Outdated flag name, may conflict with NVENC | Use `VaapiVideoDecoder` instead |
| No `--disable-gpu-driver-bug-workarounds` | Chrome applies NVIDIA workarounds that slow down GPU | Add this flag alongside `--ignore-gpu-blocklist` |

**Verified working configuration for Chrome 149+ on NVIDIA 595 + KDE Wayland:**
```ini
--ozone-platform=wayland
--use-gl=angle
--use-angle=vulkan
--ignore-gpu-blocklist
--disable-gpu-driver-bug-workarounds
--enable-gpu-rasterization
--enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks
--num-raster-threads=10
```

### NVIDIA GSP Firmware — DPMS Wake Black Screen on RTX 50 Series

GSP firmware on GB206 (RTX 5060 Ti) and other Blackwell GPUs fails DisplayPort link training during DPMS wake. The monitor's LED shows signal (white) but the screen stays black. This is a known bug across 595.xx drivers.

**Fix:** Disable GSP firmware + preserve video memory:
```ini
options nvidia NVreg_EnableGpuFirmware=0 NVreg_PreserveVideoMemoryAllocations=1
```
Requires `sudo mkinitcpio -P && reboot`.

**Alternative (if GSP must stay on):** Force software link training:
```ini
options nvidia NVreg_RegistryDwords="RMUseSwLinkTraining=1"
```

**Mitigation via DDC/CI:** Add user to `i2c` group (`sudo gpasswd -a $USER i2c`) so PowerDevil can control monitor via DDC/CI, bypassing DRM DPMS.

### Orphan Diagnostic Subprocesses

Check for stuck diagnostic processes consuming 100% CPU:
```bash
ps -eo pid,pcpu,comm,args --sort=-pcpu | head -10
```
Services like RabbitMQ can spawn `rabbitmq-diagno` subprocesses that lock up in infinite loops. Kill with `sudo kill -9 <PID>`.

### Watchdog on nohz_full cores defeats isolation

`kernel.watchdog=1` with `watchdog_cpumask=0-19` creates periodic timer interrupts on ALL cores, including nohz_full isolated cores. Fix:
```
nohz_full=0-7 watchdog_cpumask=8-19
```

### Timer migration on nohz_full systems

`kernel.timer_migration=1` lets timers bounce between cores, defeating nohz_full isolation:
```bash
echo "kernel.timer_migration=0" | sudo tee /etc/sysctl.d/99-latency.conf
sysctl -p /etc/sysctl.d/99-latency.conf
```

### WiFi IRQs may escape background pinning

iwlwifi MSI-X vectors may ignore `smp_affinity` writes and land on P-cores. Check:
```bash
cat /proc/interrupts | grep iwlwifi | awk '{for(i=2;i<=21;i++) if($i>0 && $i>10000) printf "%s → CPU%d (%d)\n", $1, i-2, $i}'
```
Extend straggler catch to include iwlwifi (same bitmask logic as NVMe straggler).

### Pitfalls
- `KWIN_TRIPLE_BUFFER=0` is a KDE5 var — does nothing on KDE6. The KDE6 equivalent is `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1`
- `nvidia-settings -a GPUPowerMizerMode=2` may silently fail on Wayland — use modprobe `NVreg_RegistryDwords` instead
- `DXVK_ASYNC=1` is obsolete on DXVK 2.x+ — use `dxvk.conf` with `dxvk.enableAsync = True`
- `LIBVA_DRIVER_NAME=nvidia` vs `nvidia_vulkan` are different backends — align them across all config files
- **VRR flicker on NVIDIA Wayland** — `VrrPolicy=Always` causes constant monitor flickering on desktop because the refresh rate fluctuates with every compositor render change. Fix: set `VrrPolicy=FullscreenOnly`. Apply via: `kwriteconfig5 --file kwinrc --group Compositing --key VrrPolicy FullscreenOnly` then reconfigure KWin or log out/in.
- **Intel IOMMU causes NVDEC0 GPU MMU faults on RTX 5000 series** — Chrome's hardware video decode triggers NVIDIA Xid 31 GPU MMU faults when `intel_iommu=on` is set. The IOMMU page tables cache structure conflicts with the GPU's internal VA space manager for NVDEC0. Removing `intel_iommu=on` resolves both the MMU faults and the associated DMA translation overhead. Disable Chrome's `--disable-accelerated-video-decode` as a workaround if IOMMU must stay on for VM passthrough.

## Keyboard Input Latency Diagnosis

End-to-end investigation methodology for diagnosing why keyboard input feels laggy on a Linux desktop (especially Alacritty/Kitty/foot terminals on Wayland + NVIDIA).

### Trigger

Use this when the user reports:
- "Keyboard feels laggy" or "input latency is high in terminal"
- Alacritty/terminal specifically has worse latency than other apps
- Key presses take perceptible time to appear on screen
- User has already checked the easy things (no input method, no heavy compositor effects)

### The Full Input Pipeline

Every keystroke must travel through approximately 8 hops from hardware to visible character:

```
Keyboard HW → USB HID → kernel input subsystem → Wayland compositor (KWin) →
wl_keyboard protocol → terminal event loop → terminal render → EGL swap →
compositor composition → NVIDIA DRM driver → Display
```

Diagnose layer by layer. Do NOT skip any layer.

### Layer 1 — Hardware Path (Keyboard + USB)

```bash
# 1a. Identify keyboard device path and USB controller
ls -la /dev/input/by-path/*-event-kbd
# Look for pci-0000:xx:xx.x-usb-...-event-kbd — the USB path tells you the controller

# 1b. Get USB vendor/product ID and HID polling interval
sudo lsusb -v -d <vendor:product> 2>/dev/null | grep -E '(bInterval|bcdUSB|HID Device)'
# bInterval=1 means 1ms USB interrupt interval (optimal)
# bInterval >1 means >1ms polling (adds baseline latency)

# 1c. Check kernel USB HID polling override
cat /sys/module/usbhid/parameters/kbpoll
# Should be 1 (1ms) — set via boot param usbhid.kbpoll=1

# 1d. Check USB autosuspend status on keyboard port
for dev in /sys/bus/usb/devices/*/product; do
  product=$(cat $dev 2>/dev/null)
  dir=$(dirname $dev)
  if [ -e "$dir/power/autosuspend" ]; then
    echo "$product: autosuspend=$(cat $dir/power/autosuspend)"
  fi
done
# autosuspend=2 means: 2s idle → USB port suspends → 3-10ms resume latency on next keypress
# autosuspend=-1 means disabled (no resume delay)
# autosuspend=0 means immediate suspend (worst for input)
```

### Layer 2 — IRQ Affinity (Where USB Interrupts Get Processed)

USB keyboard interrupts are handled by the xHCI USB controller's IRQ. If that IRQ lands on an E-core or shares a core with GPU interrupts, latency increases.

```bash
# 2a. Find USB controller IRQ numbers
cat /proc/interrupts | grep xhci_hcd
# Note the IRQ numbers (first column)

# 2b. Check which CPUs handle them
for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  echo "IRQ $irq ($(cat /proc/irq/$irq/actions 2>/dev/null)): CPU $(cat /proc/irq/$irq/smp_affinity_list 2>/dev/null)"
done

# 2c. Critical check: USB IRQ on same core as GPU IRQ?
cat /proc/interrupts | grep -E "nvidia|xhci_hcd" | awk '{print $1, $(NF-1), $NF}'
# If USB and NVIDIA share CPUs → GPU interrupts delay USB processing
```

**Key signal:** USB IRQ on an E-core (CPUs 12-19 on Arrow Lake 265K) adds inter-core latency vs. a P-core. USB IRQ sharing a core with NVIDIA GPU IRQ causes input latency spikes under GPU load.

```bash
# 2d. Fix: pin USB IRQ to a dedicated P-core
echo 2 | sudo tee /proc/irq/<N>/smp_affinity_list
# Make permanent via systemd service (see references/keyboard-input-latency-pipeline.md)
```

### Layer 3 — C-State Exit Latency

When the system is idle and the keyboard hasn't been touched, the CPU can enter deep package C-states. A keystroke IRQ must wake the CPU first.

```bash
# 3a. Check current max C-state
cat /sys/module/intel_idle/parameters/max_cstate

# 3b. Check C-state latencies
for state in /sys/devices/system/cpu/cpu0/cpuidle/state*/latency; do
  echo "$(basename $(dirname $state)): $(cat $state) us"
done

# 3c. Check C-state usage on the USB IRQ core (replace N with actual CPU)
cpupower -c N idle-info 2>/dev/null | head -20
```

**Key signal:** If `max_cstate >= 6` and the system was idle before the keystroke, the CPU exits ~500-1000µs of deep sleep before processing the IRQ. On top of USB autosuspend resume (3-10ms), this compounds.

**Fix:** `echo 4 | sudo tee /sys/module/intel_idle/parameters/max_cstate` or add `intel_idle.max_cstate=4` to kernel cmdline.

### Layer 4 — Compositor/Display Latency Budget

The Wayland compositor controls frame timing. At 165Hz, each frame is ~6ms. The compositor adds at minimum 1 frame of buffering.

```bash
# 4a. KWin compositor settings
grep -A20 '\[Compositing\]' ~/.config/kwinrc

# 4b. Verify compositor type
qdbus6 org.kde.KWin /Compositor org.freedesktop.DBus.Properties.Get \
  org.kde.kwin.Compositing compositingType

# 4c. Monitor current resolution and refresh
kscreen-doctor -o | grep -E "Modes:|Vrr|@"
```

**Signals you want:** `LatencyPolicy=LatencyLow`, `AllowTearing=true`, `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1`, triple buffering disabled at the env level.

### Layer 5 — Application-Specific Path

The terminal emulator adds its own latency on top of the compositor pipeline.

```bash
# 5a. Check whether terminal runs native Wayland or XWayland
cat /proc/$(pgrep -x alacritty | head -1)/environ 2>/dev/null | tr '\0' '\n' | \
  grep -E '^(WAYLAND_DISPLAY|DISPLAY)'
# If WAYLAND_DISPLAY is set → native Wayland (good)
# If only DISPLAY=:0 → running under XWayland (adds extra hop)

# 5b. Check terminal renderer
# Alacritty: GLES2 on OpenGL 3.3 (check binary strings)
strings /usr/bin/alacritty 2>/dev/null | grep -E 'renderer|gles|opengl' | sort -u

# 5c. Check scheduling priority
chrt -p $(pgrep -x alacritty | head -1)
# SCHED_OTHER = normal priority, can be preempted by any RR/FIFO process (including KWin)

# 5d. Check thread model — input and render on same thread?
ps -T -p $(pgrep -x alacritty | head -1) 2>/dev/null
# If main thread handles both input + rendering → a slow render blocks input
```

### Summary: Five-Fix Approach

When all layers are diagnosed, these are the five permanent fixes in priority order:

| # | Fix | Latency Saved | How |
|---|---|---|---|
| 1 | USB IRQ → P-core | 0.5-2ms | systemd service pinning xhci_hcd IRQ to a P-core |
| 2 | Limit C-states | 0.1-1ms | `intel_idle.max_cstate=4` in kernel cmdline |
| 3 | USB autosuspend off | 3-10ms intermittent | udev rule setting `power/autosuspend=-1` for keyboard by vendor:product ID |
| 4 | Remove Intel IOMMU | 0.1-0.5ms | Remove `intel_iommu=on` from kernel cmdline (also fixes NVDEC0 faults) |
| 5 | Raise terminal priority | 0.1-1ms under load | `nice -n -5` via modified .desktop file or systemd user service |

See the reference file for exact commands: `references/keyboard-input-latency-pipeline.md`

## Shell Startup Latency Debugging

When the user reports "terminal is slow," "commands take too long to process," or "Alacritty feels laggy," the root cause is often **zsh startup overhead + per-keystroke plugin processing**, not terminal emulator rendering. Diagnose the shell, not the terminal.

### Methodology

Work through these in order. Each can independently cause perceptible lag.

1. **Measure baseline startup** — `time zsh -i -c exit 2>&1`. Note any errors during init (tput failures, gitstatus failures, `can't change option: monitor`). These are signals even when timing seems fine.

2. **Find dead plugin managers** — grep for zinit/zplug/zgen. Plugin managers that are sourced but load zero plugins are dead init cost.

3. **Check for dual theme loads** — grep for `ZSH_THEME` and `powerlevel10k`. oh-my-zsh theme + p10k = first theme loaded then replaced = wasted init.

4. **Audit per-keystroke plugins** — grep `plugins=` in zshrc. Key culprits: `zsh-syntax-highlighting` (regex on every keystroke), `zsh-autosuggestions` (history search on every keystroke). Both need async mode enabled.

5. **Check async defaults** — `ZSH_AUTOSUGGEST_USE_ASYNC=1` is NOT default. Without it, autosuggestions blocks on every keypress.

6. **Kill oh-my-zsh auto-update** — `zstyle ':omz:update' mode disabled`. The auto-update check fires periodically and adds 300-500ms timeout when triggered.

7. **Force p10k async git** — `POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS=0.01` forces git status to never block the prompt. Set instant prompt to `verbose` so prompt appears before full init.

8. **Clean stale compdumps** — `ls ~/.zcompdump*` — if multiple dumps exist, `rm` them and let compinit regenerate one fresh dump on next start.

### Key signals
- 16+ `gitstatusd` processes with `-v FATAL` are NORMAL (one per terminal tab, FATAL = log level not error)
- `tput: No value for $TERM` errors only appear in non-interactive tests — real terminals have TERM set
- Oh-my-zsh update check triggers on FIRST run after touching `.zshrc` — expect one-time 600ms spike

### Reference
See `references/zsh-startup-optimization.md` for the full July 2026 session: dead zinit, dual theme, missing async, compdump cleanup.

## USB HID Polling Optimization (1000Hz Mouse/Keyboard)

The most overlooked latency fix for USB input devices. Even with `usbhid.mousepoll=1` and `usbhid.kbpoll=1` in kernel cmdline, the device's own USB `bInterval` and libinput's hwdb can override the effective polling rate.

### Three-Layer USB HID Polling Architecture

```
Layer 3 — Hardware bInterval (device-advertised)
  ↓
Layer 2 — Kernel usbhid.mousepoll/kbpoll (kernel fallback cap)
  ↓
Layer 1 — libinput hwdb MOUSE_POLL quirk (effective override)
```

**Each layer can independently cap the final rate.**

| Layer | What controls it | How to verify | How to fix |
|-------|-----------------|---------------|------------|
| 3 — Device bInterval | USB descriptor from manufacturer | `sudo lsusb -v -d <VID:PID> \| grep bInterval` (1=1ms, 6=~4ms) | Hardware-limited; gaming devices typically have bInterval=1 already |
| 2 — Kernel usbhid.mousepoll/kbpoll | Kernel params | `cat /sys/module/usbhid/parameters/mousepoll` | `usbhid.mousepoll=1 usbhid.kbpoll=1` in GRUB |
| 1 — hwdb MOUSE_POLL | udev hwdb files | `sudo libinput quirks list` or check `/etc/udev/hwdb.d/` | hwdb entry `MOUSE_POLL=1` per VID:PID |

### The hwdb Quirk (Layer 1 — Most Important)

Without hwdb, libinput assumes the device runs at its advertised bInterval (typically 125-250Hz for most peripherals). The hwdb file overrides this at the libinput level:

```bash
# /etc/udev/hwdb.d/71-corsair-polling.hwdb
# Corsair Katar Pro XT — 1000Hz
evdev:input:b0003v1b1Cp1bac* MOUSE_POLL=1

# BY Tech Thor 230 — 1000Hz (mouse + keyboard on same dongle)
evdev:input:b0003v331Ap5020* MOUSE_POLL=1
```

Apply:
```bash
sudo systemd-hwdb update && sudo udevadm trigger
```
No reboot needed. Immediate effect.

### The usbhid.quirks Kernel Param (Layer 2 Reinforcement)

`usbhid.quirks=0xVID:0xPID:0x40` — the `0x40` flag = `HID_QUIRK_ALWAYS_POLL`:

- **Without quirks**: USB device enters autosuspend when idle. On first input: resume USB (1-3ms wake latency), batch events, process. First few movement deltas lost.
- **With quirks 0x40**: Device never suspended, never enters low-power mode. Events flow at full rate with zero wake latency.
- **With `usbcore.autosuspend=-1`**: Global USB never sleeps. Complements per-device quirks.

```ini
# GRUB_CMDLINE_LINUX_DEFAULT append:
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40 usbcore.autosuspend=-1
```

### Total Effect

| Config | Effective Poll Rate | Wake Latency | Micro-Gaps |
|--------|-------------------|-------------|------------|
| Default (no hwdb, no quirks) | 125-250Hz (4-8ms) | 3-10ms on first input | Yes (drop first 2-3 events after idle) |
| hwdb only | 1000Hz (1ms) | 3-10ms on first input | Yes |
| hwdb + quirks + autosuspend | 1000Hz (1ms) | 0ms (always active) | No |

### Workflow — Adding a New USB Device

```bash
# 1. Find VID:PID
lsusb | grep -i "device_name"

# 2. Find the event device path
ls -la /dev/input/by-id/*"device_name"*

# 3. Verify current bInterval (need sudo)
# sudo lsusb -v -d <VID:PID> | grep bInterval

# 4. Add hwdb entry
sudo tee -a /etc/udev/hwdb.d/71-custom-polling.hwdb << EOF
evdev:input:b0003v<VID>p<PID>* MOUSE_POLL=1
EOF

# 5. Apply
sudo systemd-hwdb update && sudo udevadm trigger

# 6. Verify effective polling with evtest (on a mouse or keyboard event node)
# Watch event timestamps — should show ~1ms deltas during fast movement
sudo evtest --grab /dev/input/by-id/usb-...-event-mouse
# Look for sub-2ms deltas between consecutive POINTER_MOTION events during fast sweep
```

### Output Style Preference

The user for this system prefers **commands-first, terse output**. Present the exact command(s) before any explanation. The user will ask if they need clarification. When sharing tuning recommendations:

1. Show the command first: `sudo cat /sys/...` not "Let me check your current..."
2. Show the actual output next
3. Only explain if the result is unexpected
4. Avoid multi-paragraph analysis — let the numbers speak
5. **When showing pending config changes**: present as raw file content blocks, one per file, with zero commentary between them. The user will ask if they need context. Label each block with the target path.
6. **After applying writes**: verify the write actually happened (check exit code, file content, or runtime state) before reporting success. Do not rely on tool return values alone — the system verifier catches silent failures.

This applies to ALL tuning/debugging output for this user. "Show me the command and its result, then I'll ask for more" is the expected interaction pattern.

### Writing audit prompts for LLMs

When the user asks you to write a prompt that an LLM will use for system auditing, use **methodology-driven descriptions** (scope and intent per layer) rather than prescribing specific commands. Tell the LLM *what domain to audit and what to look for*, not *which exact commands to run*. This lets the LLM discover files, paths, and tools based on the actual system state rather than being boxed into pre-written commands that may not apply. Layer descriptions should define the scope, not the specific checks.

## Complete Parameter-Surface Audit (sysctl + cmdline + env)

When the user asks to "go through every config/parameter of the system and find the best" — the **full audit** — the previous two rules are hard lessons from a correction:

1. **Cover the entire parameter surface, not just the tuned layers.** Do NOT audit only My earlier tuning/the already-optimized layers. On this box `sysctl -a` reports ~3570 tunables (3300 are `net.*` per-interface noise; the meaningful set is ~340). Extract and audit the meaningful whole: `kernel.*` (~142), `vm.*` (50), `fs.*` (54), `net.core`/non-interface `net.*` (70), `user.*` (12), `dev.*` (9), `debug.*` (2), `abi.*` (1), plus `/proc/cmdline` and the CPU tunables (governor, min/max_perf_pct, epp, max_cstate). Skipping the majority is exactly the "crap, not covering 10% of what the system has" complaint.

2. **Give the researched authoritative best value — not your own verdict.** Do not emit `✅ Good` / `⚠️ Minor` opinion rows. The user specifically asked: "look online for best one", "research the answer for best option — not your takeaway". Every recommended value must carry a **real Source URL**: kernel.org (`admin-guide/sysctl/vm.html`, `kernel-parameters.html`), kernel.org kernel-internals (sysctl-reference, sched-tuning), Red Hat docs, dolpa.me sched tuning, CachyOS/Arch guides, NVIDIA forums, Proton docs. If no source is found for a parameter, say "no authoritative source found" rather than invent a value.

### Workflow

1. **Make the plan first** (the user insists: "make the plan first, a complete one"). Enumerate every layer up front.
2. **Extract the full baseline to files** (do not eyeball):
   ```bash
   mkdir -p ~/audit
   sysctl -a 2>/dev/null | grep -vE "^net\.(ipv4|ipv6|core|bridge|nf_conntrack)" > ~/audit/current_sysctl.txt
   cut -d= -f1 ~/audit/current_sysctl.txt | awk -F. '{print $1}' | sort | uniq -c   # group counts
   cat /proc/cmdline > ~/audit/current_cmdline.txt
   { echo "governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"; \
     echo "driver=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver)"; \
     echo "min_perf=$(cat /sys/devices/system/cpu/intel_pstate/min_perf_pct)"; \
     echo "max_perf=$(cat /sys/devices/system/cpu/intel_pstate/max_perf_pct)"; \
     echo "epp=$(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference)"; } > ~/audit/current_cpu.txt
   ```
3. **Delegate the per-parameter research to a subagent** rather than doing 350 lines of web research inline. Hand the subagent the baseline file paths + the use-case context + output format, and instruct it: for EACH parameter find the authoritative best value with a real source URL; group "leave at default" ones; also recommend MISSING cmdline tokens. Give it the sourced prompt template — see `references/complete-parameter-audit.md`.)
4. **Report**: one sourced table per group (`Parameter | Current | Recommended | Source URL | Notes`). Flag genuinely actionable issues (e.g. THP `always`+`always`, per-core C-state disable not persisting, gamemoded not running, contradictory KWin triple-buffer env). Write proposed configs to `~/` as review-only files and **do not apply anything without explicit approval.**

### User expectations (hard)
- **Plan before acting** — user will call out if you drift into collection/research without presenting the plan.
- **Full surface** — incomplete coverage is rejected immediately and harshly.
- **Sourced best value, not opinion** — a verdict-without-research row is a miss.
- **Commands-first, terse output**; when presenting pending changes, show raw file content blocks labeled with target paths, zero commentary between them. (See Output Style Preference above.)
- After any applied write, verify it landed (file content / runtime state) before reporting success.

## Workstation + Desktop + Gaming Comprehensive Tune-Up

When the user asks for "all tweaks" or a complete system tune-up covering workstation, desktop responsiveness, AND gaming, use the following layered approach. Each layer is a self-contained batch of copy-paste commands.

### The Nine-Layer Tuning Stack

| Layer | Focus | Impact |
|-------|-------|--------|
| 1 — Kernel & Scheduler | linux-zen/cachyos, scx_lavd, preempt=full | Every interaction |
| 2 — Memory & VM | swappiness, huge pages, ZRAM | Large workloads |
| 3 — Storage & I/O | NVMe scheduler, noatime, TRIM | Storage responsiveness |
| 4 — KDE Compositor | triple buffering, VRR, animation speed | Desktop feel |
| 5 — NVIDIA Compute | persistence mode, PowerMizer, CUDA env | GPU throughput |
| 6 — CPU Governor | schedutil/performance, auto-cpufreq | Power/performance |
| 7 — PipeWire Audio | quantum tuning, WirePlumber config | Audio latency |
| 8 — Service Reduction | bluetooth, cups, indexing, journal | More RAM/CPU |
| 9 — Compiler & Build | makepkg, ccache, RAM-based build dir | Faster compiles |

Execute layers in order. Each layer is independent — no batch-ordering dependencies.

See `references/workstation-desktop-gaming-tuning-2026.md` for the full command reference.

### WirePlumber 0.5 vs 0.4 Config — Known Pitfall

WirePlumber **0.5+** uses `.conf` files in `wireplumber.conf.d/` with SPA-JSON syntax, NOT Lua tables in `main.lua.d/`.

| Version | Config Dir | Syntax | Example |
|---------|-----------|--------|---------|
| 0.4.x | `main.lua.d/` | Lua `table.insert(alsa_monitor.rules, ...)` | Old (broken on 0.5+) |
| **0.5.x** | **`wireplumber.conf.d/`** | **`monitor.audio.rules = [ { matches = [...], actions = {...} } ]`** | **Current** |

**Wrong (0.4 syntax, will error on 0.5):**
```lua
-- ~/.config/wireplumber/main.lua.d/51-chrome-low-latency.lua
rule = {
  matches = [ { { "application.name", "equals", "chrome" } } ],
  apply_properties = { ["node.quantum"] = 256 },
}
table.insert(alsa_monitor.rules, rule)
```

**Correct (0.5 syntax):**
```ini
# ~/.config/wireplumber/wireplumber.conf.d/51-chrome-quantum.conf
monitor.audio.rules = [
  {
    matches = [ { application.name = "Google Chrome" } ]
    actions = { update-props = { node.quantum = 256 } }
  }
]
```

Always check `wireplumber --version` first to determine which API to use. If version ≥ 0.5, use `.conf` in `wireplumber.conf.d/`.

### LACTD Polling — Micro-Stutter Source

LACTD (Linux GPU Control Daemon) polls GPU sensors for fan curves every `interval_ms` and reapplies the full config every `apply_settings_timer` seconds. Default values (500ms interval, 5s reapply) cause periodic PCIe register reads/writes that can manifest as micro-stutters in games.

```bash
# Check current config
cat /etc/lact/config.yaml | grep -E 'interval_ms|apply_settings_timer'

# Saner values for gaming (2s polling, 30s reapply)
# Edit /etc/lact/config.yaml:
#   interval_ms: 2000
#   apply_settings_timer: 30
sudo nano /etc/lact/config.yaml
sudo systemctl restart lactd
```

If you're not doing dynamic fan control at all, just stop lactd entirely:
```bash
sudo systemctl disable --now lactd.service
```

### nvidia_drm fbdev=1 on Wayland — Wasted VRAM

The `nvidia_drm` kernel module with `fbdev=1` allocates a shadow framebuffer in VRAM and runs a console emulator (`/dev/fb0`) that nobody reads on a Wayland-only desktop. Every frame the emulator polls adds unnecessary GPU-CPU sync traffic.

Check:
```bash
cat /sys/module/nvidia_drm/parameters/fbdev  # 1 = enabled
ls -la /dev/fb*  # /dev/fb0 exists
```

Fix on Wayland-only systems:
```bash
# Set fbdev=0 in modprobe.d
echo 'options nvidia_drm modeset=1 fbdev=0' | sudo tee /etc/modprobe.d/nvidia-drm.conf
sudo mkinitcpio -P && reboot
```

### Pitfalls

### DON'T Write System Files During Investigation
- **`MOUSE_POLL=1` also affects keyboards** on multi-interface dongles (e.g., a wireless mouse+kb combo may have one USB interface for both). Apply the quirk to the mouse's event path and the keyboard event path on the same device.
- **usbhid.mousepoll/kbpoll are kernel FALLBACKS**, not overrides. If the device's firmware-advertised bInterval is 6 (4ms), and no hwdb entry exists, the kernel respects the device's value even if mousepoll=1.
- **`power-profiles-daemon` silently overrides CPU governor**. Even with `cpufreq.default_governor=performance` in GRUB, PPD can change it to `powersave` at any time. **Always disable PPD** on a low-latency workstation: `sudo systemctl disable --now power-profiles-daemon`. Verify: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor` shows `performance`.
- **GRUB edits can silently fail to persist** when:
  1. Running `grub-mkconfig` but the output goes to the wrong path (check `grub-mkconfig -o /boot/grub/grub.cfg` vs systemd-boot's `/boot/loader/entries/`)
  2. A kernel update regenerates grub.cfg from the current grub defaults, overwriting manual changes
  3. Editing `GRUB_CMDLINE_LINUX_DEFAULT` vs `GRUB_CMDLINE_LINUX` (they concatenate at boot — missing params may be in the wrong line)
  **Safest workflow**: edit `/etc/default/grub`, then run `sudo grub-mkconfig -o /boot/grub/grub.cfg`, then **reboot and verify**: `cat /proc/cmdline | grep <param>`. Do not rely on the GRUB file alone.
- **xinput does NOT work on Wayland**. For input debugging on KDE Wayland, use `sudo libinput debug-events` or `sudo evtest`. `xinput list-props` returns nothing for Wayland devices.

### Reference file

See `references/usb-hid-polling-1000hz.md` for session-specific reproduction commands and a real-world Corsair Katar Pro XT + BY Tech Thor 230 configuration.

## Network Latency Tuning

### WiFi Hardware Investigation — Full Methodology

When investigating a WiFi adapter's performance, probe these layers in order:

#### Layer 1 — Hardware & Driver Identification
```bash
# Card, vendor, PCI location
lspci -vnn | grep -i network
# Driver and firmware in use
ethtool -i wlpX
# Module parameters (iwlwifi + iwlmld — separate drivers on new Intel cards)
cat /sys/module/iwlwifi/parameters/*
cat /sys/module/iwlmld/parameters/*
# Firmware files loaded
dmesg | grep -i 'iwlwifi\|iwlmld'
```

#### Layer 2 — Link Quality & Connection Cap
```bash
# SSID, freq, channel width, signal, bitrate, MCS/NSS
iw dev wlpX link
iw dev wlpX station dump
iw dev wlpX info
# Survey dump for noise floor on active channel
iw dev wlpX survey dump
# Regulatory domain
iw reg get
iw list | grep -E 'Band|frequencies|MHz|widths|160|6 GHz|320'
```

Key signals:
- **Signal < −70 dBm**: marginal link, reposition or check antennas
- **Channel width < AP capability**: check for DFS interference or regulatory limits
- **Rate < expected**: AP may be limiting (check if VHT, HE, or EHT is negotiated)
- **TX retries > 0.1%**: interference or power save transitions

#### Layer 3 — iwlwifi/iwlmld Module Parameter Tuning

For Intel BE200/BE202 (Bz family) and similar iwlwifi cards:

| Param | Module | Default | Performance | Why |
|-------|--------|---------|-------------|-----|
| `power_save` | iwlwifi | N | N | mac80211 PS off |
| `bt_coex_active` | iwlwifi | Y | **0** | When BT is soft-blocked, coexistence still reserves airtime — wastes throughput |
| `disable_11be` | iwlwifi | N | **1** | Avoids unstable WiFi 7 codepaths on Bz hardware (known bug: Queue stuck / NMI_INTERRUPT_UNKNOWN) |
| `uapsd_disable` | iwlwifi | 3 | **3** | Bitmask: 1=BSS, 2=P2P Client; 3 disables both |
| `power_scheme` | **iwlmld** | 2 (BIST) | **1 (CAM)** | **Most impactful.** Controls device-level PCIe power gating independently of mac80211 PS. CAM keeps the PCIe link active — eliminates L1 substate transition latency |

Create `/etc/modprobe.d/iwlwifi.conf`:
```
options iwlwifi power_save=0 bt_coex_active=0 disable_11be=1 uapsd_disable=3
options iwlmld power_scheme=1
```

Then rebuild initramfs: `sudo mkinitcpio -P` (Manjaro/Arch), `sudo update-initramfs -u` (Debian/Ubuntu), `sudo dracut -f` (Fedora). Requires reboot.

**Pitfall**: `pcie_aspm=off` kernel cmdline is **NOT sufficient** on modern platforms — ACPI _OSC can override it. On BE200/BE202, PCI-level ASPM disable via `setpci` for both endpoint and upstream bridge is the reliable fix when module params alone don't stabilize the link. See `references/wifi-intel-be200-be20x-investigation.md`.

#### Layer 4 — IRQ Distribution & CPU Affinity

Check if all WiFi MSI-X vectors are landing on one CPU:
```bash
# View iwlwifi interrupt counts per CPU
cat /proc/interrupts | grep iwlwifi
# Pin to specific core bank (e.g., E-cores 12-19 on a hybrid system)
echo 12 > /proc/irq/210/smp_affinity_list
```

See the IRQ Affinity section above for the full pinning script.

#### Layer 5 — Path MTU Discovery

WiFi often has a lower-than-1500 MTU due to router WAN caps or ISP overhead. The current interface MTU may be suboptimal:

```bash
# 1. Check current interface MTU
ip link show wlpX | grep mtu

# 2. Probe path MTU to WAN
ping -M do -c 3 -s 1444 8.8.8.8   # payload = MTU - 28 (IP+ICMP); 1472 = full 1500
ping -M do -c 3 -s 1392 8.8.8.8   # 1420 MTU test (common WiFi default)

# 3. If Frag needed is returned, router tells you the limit:
# "From 192.168.0.1 icmp_seq=1 Frag needed and DF set (mtu = 1472)"

# 4. Test local gateway at full 1500
ping -M do -c 3 -s 1472 192.168.0.1

# 5. Apply optimal MTU
sudo ip link set dev wlpX mtu <discovered_value>
```

Each +52 bytes saved = ~3.5% throughput gain on bulk TCP flows.

### WiFi-specific Rules Summary
- **Modprobe** params (iwlwifi + iwlmld) control driver-level power — these are SEPARATE from runtime `iw dev power_save`
- **Runtime** `iw dev wlpXXX set power_save off` is mac80211 PS — still check both
- **iwlmld power_scheme=1 (CAM)** is the real fix for L1 latency on BE20x cards
- `bt_coex_active=0` when Bluetooth is unused/blocked
- `disable_11be=1` is a stability workaround for WiFi 7 hardware on current firmware
- Default qdisc is `noqueue` — `fq_codel` adds bufferbloat protection
- Path MTU can be 52-80 bytes below 1500 due to WiFi overhead + router caps — probe it

### Reference
See `references/wifi-intel-be200-be20x-investigation.md` for the full session-specific research: firmware versions, iwlmld power_scheme CAM source analysis, BE200/BE202 instability background, discovered MTU values, and the complete commands reference.

### Native Game Input Lag Diagnosis

See `references/native-game-input-lag-diagnosis.md` for diagnostic patterns specific to **native Linux games** (non-Proton) running through Steam's pressure vessel — Dota 2 / Source 2, native Vulkan/OpenGL titles. Covers GPU/CPU utilization imbalance diagnosis (smoking gun: GPU <15% with CPU >200%), Intel Arrow Lake 265K / NVIDIA + Wayland, Steam Linux Runtime CPU affinity check, game thread priority analysis via `/proc/[pid]/task/*/stat`, Dota 2 launch options (`-vulkan -high`), KWin compositor gaming settings (WindowsBlockCompositing, AllowTearing, VrrPolicy, LatencyPolicy), EasyEffects blocklist for game audio, full IRQ topology dump per-CPU, PipeWire quantum under game load, and NVIDIA Wayland env verification. Use when investigating input lag in a native Linux game where the render API is direct (not DXVK/VKD3D) and Steam's pressure vessel restricts CPU affinity.

### TCP Tuning for Low Latency + Throughput

```ini
net.ipv4.tcp_congestion_control=bbr
net.core.default_qdisc=fq
net.ipv4.tcp_notsent_lowat=131072       # Allows send without ACK wait
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0    # Don't reset cwnd after idle pauses
net.ipv4.tcp_mtu_probing=1              # Enable PMTU discovery
net.core.rmem_default=262144            # BDP for 350Mbps × 5ms ≈ 219KB
net.core.wmem_default=262144            # Same as rmem
```

Apply via `/etc/sysctl.d/90-wifi-performance.conf` and `sudo sysctl -p /etc/sysctl.d/90-wifi-performance.conf`.

### Write Verification

After using `sudo tee` or any file-write command to install tuning configs, ALWAYS verify the write landed before informing the user:

```bash
# Verify file content matches what was intended
cat /etc/modprobe.d/iwlwifi.conf
cat /etc/sysctl.d/90-wifi-performance.conf

# Verify runtime state reflects the change
sysctl net.ipv4.tcp_mtu_probing
iw dev wlpX get power_save
cat /sys/module/iwlmld/parameters/power_scheme
```

Sudo may silently fail (no password provided, cached credentials expired). Do not assume write success from a zero exit code — check via a subsequent read. The File-mutation verifier in Hermes catches unverified writes; be explicit about confirmation."
