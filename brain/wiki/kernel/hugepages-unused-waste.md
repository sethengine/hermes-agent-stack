---
source: 20260703_231509_6397bb
category: kernel
date: 2026-07-03
tags: [hugepages, memory, waste, unused, locked-ram]
---

# Unused HugePages Waste 16 GB of RAM

On a desktop with no VMs (QEMU/KVM), no DPDK, and no database requiring hugepages, 8192 × 2M hugepages consume 16 GB of locked physical RAM that is never used.

**Symptoms:** `/proc/meminfo` shows `HugePages_Total=8192`, `HugePages_Free=8192` — all 16 GB allocated but 100% unused. This RAM is unavailable for disk cache, Chrome, Steam, games, or any application.

**Root cause:** Previously set `hugepagesz=2M nr_hugepages=8192` in GRUB_CMDLINE_LINUX_DEFAULT for latency testing, but never removed. On this system, `transparent_hugepage=madvise` uses the separate THP pool, not the persistent HugePages pool.

**Fix — remove from kernel cmdline:**
1. Edit `/etc/default/grub`, remove `hugepagesz=2M nr_hugepages=8192`
2. `sudo grub-mkconfig -o /boot/grub/grub.cfg`
3. Reboot

**Verification:** After reboot, `cat /proc/meminfo | grep HugePages_Total` should show 0.

[[hugepages-for-latency]]
[[intel-arrow-lake-kernel-cmdline-tuning]]
