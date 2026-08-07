---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: kernel
tags: [hugepages, memory, latency, grub, kernel]
---

# Hugepages Pre-Allocation for Memory Allocation Latency

Pre-allocating 2M hugepages reduces page fault overhead for applications like Firefox, Alacritty, and VSCode. Added to GRUB cmdline:

```
hugepagesz=2M nr_hugepages=8192
```

This reserves ~16GB of the 64GB RAM as 2M pages upfront. Combined with transparent hugepages=madvise (kernel default), applications using madvise(MADV_HUGEPAGE) get faster allocations.

To apply: append to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then `sudo grub-mkconfig -o /boot/grub/grub.cfg` and reboot. Verify with `cat /proc/meminfo | grep Hugepages_Total`.

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
