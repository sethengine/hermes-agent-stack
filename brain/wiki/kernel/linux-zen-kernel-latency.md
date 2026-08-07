---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: kernel
tags: [kernel, zen, latency, eevdf, scheduler, manjaro]
---

# Linux-Zen Kernel for Lower Scheduling Latency

The linux-zen kernel provides lower scheduling latency via EEVDF scheduler (compared to the default 6.18 kernel's preempt=voluntary). On Manjaro:

```bash
sudo mhwd-kernel -i linux-zen   # Install and set as default
sudo reboot
```

Expected improvement: scheduling latency drops from ~313µs to <100µs for typing/console responsiveness. Alternative: linux-rt-lts (preempt=full) for even lower but potential throughput reduction.

Current system uses only linux618 kernel — adding zen provides a boot option for lower latency while keeping stock as fallback.

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[hugepages-for-latency]]
