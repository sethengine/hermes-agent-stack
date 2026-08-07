---
source_session: "20260703_202938_ecafcd"
date: "2026-07-03"
category: software
tags: [low-latency-layer, nvidia, reflex, vulkan, gaming-latency, proton]
---

# low_latency_layer + NVIDIA Native Reflex Conflict

**Problem:** On NVIDIA GPUs with Reflex support (RTX 30/40/50 series, driver 570+), the open-source `low_latency_layer` Vulkan layer competes with the NVIDIA driver's native `VK_NV_low_latency2` implementation.

When both are active:
- The layer intercepts Reflex state calls **and** the native driver also processes them
- GPU receives conflicting Reflex state → frametime spikes or TDR crashes
- This is especially bad in games with aggressive Reflex integration (Dead Space Remake, Call of Duty, Overwatch 2)

**Rule of thumb:**
| GPU | Reflex provider | Use low_latency_layer? |
|-----|---------------|----------------------|
| RTX 30/40/50 series | Native NVIDIA driver (570+) | ❌ Not needed, causes conflicts |
| AMD | No native Reflex | ✅ Yes, adds Reflex support |
| Intel Arc | No native Reflex | ✅ Yes, adds Reflex support |
| Older NVIDIA (< RTX 30) | Partial native | ⚠️ Test per-game |

**For NVIDIA with native Reflex:** Use `PROTON_ENABLE_NVAPI=1` alone. The driver handles Reflex natively without the Vulkan layer.

[[dead-space-remake-proton-directx-crash]] [[proton-gaming]] [[nvidia-wayland]]
