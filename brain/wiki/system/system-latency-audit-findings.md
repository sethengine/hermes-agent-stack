---
source_session: "20260709_193718_2e6307"
date: "2026-07-09"
category: system
related: [latency, kernel, nvidia, pipewire, irq, sysctl]
---

# Comprehensive System Latency Audit (July 2026)

Full scan of a Manjaro Linux desktop (kernel 7.0.10-1-MANJARO, Intel Ultra 7 265K, NVIDIA RTX 5080, 64GB DDR5) for input/audio latency:

**Working well:** preempt=full ✅, threadirqs ✅, performance governor ✅, usbhid polling=1 ✅, cyclictest max 92µs ✅, IRQ pinning (NVIDIA→E-cores, USB→E-cores) ✅, GPU clocks 2722/13801 MHz ✅, KWin direct scanout ✅, NMI watchdog off ✅, workqueue power_efficient=false ✅.

**Issues found:**
1. **CRITICAL:** [[grub-param-concat-bug-aspm]] — missing space broke ASPM policy
2. **HIGH:** [[pipewire-config-chaos-quantum-conflicts]] — 4 conflicting configs, 21.3ms latency
3. **MEDIUM:** NVMe power/control=auto on both drives — PS transitions add ~5-10µs
4. **MEDIUM:** `vm.swappiness` set to both 5 and 10 in different sysctl files
5. **LOW:** [[nvidia-modprobe-duplicate-options]] — duplicated options blocks
6. **INFO:** Zombie keyd process (PID 907) still running despite masked systemd unit
7. **INFO:** KWin D-Bus interface unresponsive after config change

[[latency-tuning]] [[system-performance-audit]]
