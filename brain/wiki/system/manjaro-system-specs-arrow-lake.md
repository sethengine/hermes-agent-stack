---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: system
tags: [system, hardware, manjaro, arrow-lake, specs]
---

# Manjaro System Specs: Arrow Lake + NVIDIA RTX 5060 Ti

Full hardware/software specification of the workstation:

- **OS**: Manjaro (Arch-based) with KDE Plasma 6.5.6, Wayland (kwin_wayland)
- **Kernel**: 6.18.18-1-MANJARO (PREEMPT_DYNAMIC, preempt=voluntary)
- **CPU**: Intel Core Ultra 7 265K (20-core Arrow Lake, up to 6.5GHz P-cores, no SMT, single NUMA node)
- **GPU**: NVIDIA GeForce RTX 5060 Ti (driver 590.48.01, CUDA 13.1, 16GB VRAM)
- **RAM**: 64GB (62GB available)
- **Storage**: WD SN850X 2TB NVMe + Kingston 1TB NVMe (kyber I/O scheduler)
- **Display**: HP X34 3440x1440 @ 165Hz ultrawide
- **Network**: WiFi 7 Intel AX1775
- **Audio**: PipeWire
- **Motherboard**: Gigabyte Z890 AERO G (BIOS F17f, 07/2025)
- **Session**: SDDM display manager

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[nvidia-wayland-kwin-latency-policy]]
