---
source: session 20260609_195359_ab296b (Keyboard Input Latency Investigation)
date: 2026-06-09
category: system/
---

# Keyboard Input Latency Investigation — System Findings

System configuration discovered during input latency investigation on a Manjaro workstation with KDE Plasma 6, Wayland, and NVIDIA RTX 5060 Ti.

## Key Findings

| Component | Detail | Impact |
|---|---|---|
| **CPU** | Intel Core Ultra 7 265K (Arrow Lake, 20C/20T — no hyperthreading) | E-cores (12-19) are slower than P-cores (0-7); IRQ affinity matters |
| **Kernel** | 7.0.10-1-MANJARO, `preempt=full`, CONFIG_HZ=1000 | Good baseline — full preemption |
| **Cmdline** | `nohz_full=0-7 rcu_nocbs=0-7` | Isolates P-cores from housekeeping |
| **IOMMU** | `intel_iommu=on,igfx_off iommu=pt` | Adds DMA translation overhead |
| **Display** | NVIDIA RTX 5060 Ti, 595.71.05 driver, KDE Wayland, KWin | KWin compositor uses `egl` backend |
| **Alacritty** | v0.17.0, runs on Wayland, uses GLES2 renderer | SCHED_OTHER (default), no real-time prio |
| **USB keyboard** | BY Tech Thor 230 (331a:5020), USB polling = 1ms | `usbhid.kbpoll=1` already set |
| **USB mouse** | Corsair KATAR PRO XT (1b1c:1bac) | `usbhid.mousepoll=1` already set |
| **KWin** | LatencyPolicy=LatencyLow, AllowTearing=true, VRR=FullscreenOnly | Compositing is ON for windows |

See also: [[irq-pinning-usb-to-pcore]], [[usb-input-autosuspend-disable]], [[iommu-latency-impact]]
