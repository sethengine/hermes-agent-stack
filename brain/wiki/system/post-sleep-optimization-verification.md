---
source: 20260502_150358_5e17d2
category: system
date: 2026-07-06
tags: [sleep, wake, verification, checklist, optimization, persistence]
---

# Post-Sleep Optimization Verification Checklist

After S3 sleep/wake, verify latency optimizations survived:

```bash
# GRUB cmdline params
cat /proc/cmdline | tr ' ' '\n' | grep -E "preempt|usbhid|threadirqs|pcie_aspm|cstate"

# CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Hugepages
grep HugePages_Total /proc/meminfo

# Sysctl
sysctl kernel.sched_rt_runtime_us vm.swappiness

# USB polling
grep . /sys/module/usbhid/parameters/*poll*

# NVIDIA P-state
nvidia-smi -q -d PERFORMANCE | grep "Performance State"

# KWin compositing (always ON under Wayland — can't disable)
kreadconfig5 --file kwinrc --group Compositing --key Enabled

# power-profiles-daemon (should be disabled)
systemctl is-active power-profiles-daemon

# Resume hook ran?
journalctl -b | grep "latency-fix" | tail -1
```

## Known Post-Sleep Degradations
- Hugepages drop from 2048 → 512 (memory fragmentation)
- Display colors wash out (RGB range limited → needs DPMS cycle)
- [[hugepages-sleep-compact-memory]]
- [[hugepages-aggressive-sleep-recovery]]
- [[nvidia-wayland-display-color-after-sleep]]
