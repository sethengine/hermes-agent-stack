---
source: 20260706_194614_c828c3
category: gpu
date: 2026-07-12
tags: [nvidia, powerd, dynamic-boost, laptop, desktop, power-management, fps-limiting]
---

# nvidia-powerd: Laptop-Only Dynamic Boost (Not Compatible with Desktop GPUs)

`nvidia-powerd` implements NVIDIA **Dynamic Boost** — shifting power between CPU and GPU within a shared thermal/power budget. It is **laptop-only** and exits immediately on desktop systems.

## What it does

- Monitors GPU utilization and adjusts power allocation between CPU and GPU
- Only useful when both chips share a cooler and power adapter (laptop form factor)
- Supported on Ampere+ GPUs in notebook form factor

## Desktop behavior

On desktop GPUs (tested on RTX 5060 Ti, PCI ID `0x2d04`):
```
ERROR! Running on an unsupported system (PCI device Id: 0x2d04)
Quit successfully
```

The binary starts, detects the GPU is not a laptop GPU, and exits within ~28ms. It does **not** control any power management on desktops.

## Why desktop GPUs are unsupported

Desktop GPUs have:
- Independent power connectors (no shared CPU/GPU power budget)
- Independent cooling (no shared thermal budget)
- No Dynamic Boost hardware path (SBIOS support required)

Official NVIDIA documentation (`dynamicboost.html`) lists **Notebook form factor** as hardware requirement #1.

## Related false correlation

GPU utilization drops (e.g., 99% → 60%) when enabling features like MangoHud's `fps_limit` are **not** from nvidia-powerd — they are from the frame limiter doing its job. A capped frame rate requires less GPU utilization.

## References
- [[geforce-rtx-5060-ti]]
- [[mangohud-fps-limiting-proton]]
- [[linux-gaming-frame-limiters]]
- [[vulkan-fps-cap-methods]]
