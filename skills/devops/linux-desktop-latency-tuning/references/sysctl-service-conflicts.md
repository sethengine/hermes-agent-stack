# Detecting Conflicting Post-Boot Writers (tuning knobs)

How an audit discovered that the intended tuning was silently clobbered, and how to
find these fights on any system. Real case from 2026-07 audit (Manjaro, Z890,
intel_pstate, KDE Wayland).

## The core pattern

Every low-latency recipe sets values via GRUB (boot-time), systemd services
(boot-time), or sysctl.d (boot-time). These can CONFLICT:

- Multiple systemd oneshot services writing the same `/sys` knob
- A service writing a value AFTER sysctl.d was applied
- A post-boot daemon (zram setup, power daemon) overriding sysctl.d values

**The service that starts LAST wins.** A value set correctly at 17:54:41 can be
clobbered at 17:54:49 by a stale service.

## Detection recipe

### 1. Batch-compare runtime vs config intent

```bash
# runtime values
cat /proc/sys/vm/swappiness /proc/sys/vm/vfs_cache_pressure /proc/sys/vm/min_free_kbytes \
    /proc/sys/vm/max_map_count /proc/sys/vm/dirty_writeback_centisecs /proc/sys/vm/page-cluster

# config intent (list every file, lexical order = apply order)
for f in /usr/lib/sysctl.d/*.conf /etc/sysctl.d/*.conf; do echo "== $f"; done

# verify one knob actually applied (proves the file was processed):
# max_map_count=262144 from 99-performance.conf while swappiness ≠ its 10 → post-boot writer exists
```

Any runtime value matching NO config file (or matching a lower-precedence file)
means a post-boot writer. If values from 99-* DID apply but a sibling value did
not, the override is runtime, not config.

### 2. Boot-order forensics for service fights

```bash
journalctl -b | grep -E 'intel-min|cpu-perf|thp-tune|rtirq|pin-irqs'
# Shows each service's ExecStart start_time — the LAST one writing a knob wins.
systemctl show <svc> -p ExecStart --no-pager   # confirm what each writes
```

Real example: `cpu-perf-boot.service` (min_perf_pct=70) and `cpu-perf-tune.service`
(70) both started 17:54:41; `intel-min-perf.service` (min_perf_pct=25) started
17:54:49 — it clobbered the intended 70. Runtime showed 25. Fix: disable the
stale service, re-apply `echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct`.

### 3. Hidden 600-perm sysctl.d files

```bash
sysctl --system 2>&1 | grep 'Permission denied'   # as non-root user
# "cannot open /etc/sysctl.d/90-wifi-performance.conf: Permission denied"
# → file is root:root 600; agent can't read it, but systemd-sysctl (root) CAN.
# It sorts BEFORE 99-* so it loses to 99-* on shared keys — but it's still
# worth flagging as an unknown writer candidate.
stat -c '%y %n' /etc/sysctl.d/*.conf | sort   # recently-added files = suspects
```

### 4. zram — swappiness mystery, TWO cases

Runtime `vm.swappiness=150` matched NO sysctl.d file (cachyos=100, 99-perf=10).
The writer is a **udev rule, not a service or sysctl.d** (confirmed 2026-08):

```bash
grep -r 'SYSCTL{vm.swappiness}' /usr/lib/udev/rules.d/ /etc/udev/rules.d/
# /usr/lib/udev/rules.d/30-zram.rules (CachyOS/Manjaro):
#   ACTION=="change", KERNEL=="zram0", ATTR{initstate}=="1", SYSCTL{vm.swappiness}="150", ...
```

The rule fires on every zram device init event — `udevadm trigger` RE-FIRES it, so
`sysctl -w` gets clobbered again. **udev rule edits only take effect after
`udevadm control --reload` AND a NEW matching event** — editing the rule file does
NOT retroactively apply to an already-fired event (this confused the 2026-08 audit:
rule file changed to 10, runtime still 150, because the boot-time event already ran
with the old rule set).

**Case A — high-RAM desktop (64GB+): zram is pointless. Kill it entirely.**
The distro default zram moved 8 GB of a 64 GB machine's hot game pages into
compressed swap while 38 GB RAM sat free → stutter/input lag. Fix (no reboot):

```bash
# shadow the rule (higher-precedence file wins)
printf 'ACTION=="change", KERNEL=="zram0", ATTR{initstate}=="1", SYSCTL{vm.swappiness}="10"\n' \
  | sudo tee /etc/udev/rules.d/30-zram.rules >/dev/null
sudo udevadm control --reload
sudo swapoff /dev/zram0 2>/dev/null || true
echo 10 | sudo tee /proc/sys/vm/swappiness
# permanent: /etc/sysctl.d/99-swappiness-low.conf → vm.swappiness = 10
# stop it coming back at boot:
sudo systemctl mask zramswap.service 2>/dev/null || true
sudo systemctl mask systemd-zram-setup@zram0.service 2>/dev/null || true
# Arch/Manjaro: empty /etc/systemd/zram-generator.conf (or mask the generator unit)
```
Verify: `swapon --show` shows only the disk swap; `cat /proc/sys/vm/swappiness` → 10.

**Case B — genuinely low-RAM machine (≤16GB): zram IS intentional.**
Compressed RAM swap is fast there; eager swapping (150-180) is optimal.
Leave it. Only disk-swap systems want swappiness=5. The old "never fix it"
advice in this file was WRONG for high-RAM desktops — gate on RAM size, not just
zram presence.

## Other silent-failure knobs observed

| Knob | Silent failure mode | Check |
|------|--------------------|------|
| `energy_performance_preference` | Write ignored while governor=performance (script's powersave→set→performance workaround also fails) | `cat /sys/devices/system/cpu/cpuN/cpufreq/energy_performance_preference` — shows `default`, not `performance` |
| `rtirq` RT priorities | rtirq.conf malformed AND `threadirqs` absent from cmdline → service "active (exited)" but does nothing | `journalctl -b \| grep rtirq` for "A realtime kernel or the threadirqs kernel parameter are required" and conf parse errors |
| WiFi runtime power save | Driver param `power_save=0` in modprobe.d, but mac80211 runtime still `on` | `iw dev wlp... get power_save` (separate layer from module param) |
| keyd presence | Keyd re-enabled despite config notes saying masked; runs SCHED_FIFO 49, `[ids] *` grabs all keyboards | `systemctl is-active keyd`; `ps -o cls,rtprio -p <keyd pid>` |

## Verify-after-fix pattern

```bash
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct        # expect 70, not 25
cat /proc/sys/vm/swappiness                                  # expect 5 ONLY if no zram
grep -c threadirqs /proc/cmdline                              # expect 1 after GRUB change
```
