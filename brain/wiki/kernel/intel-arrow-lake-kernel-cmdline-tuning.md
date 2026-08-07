---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: kernel
tags: [kernel, cmdline, arrow-lake, latency, grub, intel, cpu]
---

# Intel Arrow Lake Kernel Cmdline Tuning for Low Latency

The system (Intel Core Ultra 7 265K, 20-core Arrow Lake) runs kernel 6.18.18-1-MANJARO PREEMPT_DYNAMIC. The heavily tuned GRUB cmdline includes:

```
cpufreq.default_governor=performance preempt=voluntary usbhid.mousepoll=1 usbhid.kbpoll=1
pcie_aspm=off pcie_aspm.policy=performance threadirqs futex_waitv=1
workqueue.power_efficient=false intel_pstate=active tsx=on
pci=pcie_bus_perf pcie_ports=native vdso=2 skew_tick=1
sched_itmt_enabled=1 intel_iommu=on,igfx_off iommu=pt
nvidia_drm.modeset=1 nvidia_drm.fbdev=1
modprobe.blacklist=iTCO_wdt udev.log_priority=3
```

Additional proposed params (pending reboot): `nohz_full=0-7 rcu_nocbs=0-19 isolcpus=4-19 mitigations=off` for further latency reduction.

Key insight: Arrow Lake has no SMT, 20 physical cores (P-cores 0-7, E-cores 8-19), single NUMA node. Already at preempt=voluntary with performance governor.

## References
- [[usbhid-low-latency-quirks]]
- [[linux-zen-kernel-latency]]
