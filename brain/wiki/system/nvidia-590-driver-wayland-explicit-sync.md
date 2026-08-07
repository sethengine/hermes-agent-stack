---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: gpu
tags: [nvidia, driver, wayland, explicit-sync, modeset, gpu]
---

# NVIDIA Driver 590 Wayland Explicit Sync Setup

NVIDIA driver 590.48.01 (CUDA 13.1) supports explicit sync on Wayland, critical for tear-free rendering with KDE Plasma 6.5.6. Kernel modules loaded: `nvidia_drm`, `nvidia_modeset`, `nvidia_uvm`.

Key kernel parameters:
- `nvidia_drm.modeset=1` — enables DRM kernel mode setting
- `nvidia_drm.fbdev=1` — enables fbdev fallback

Current performance state is P0 (maximum, no throttling). The `nvidia_drm` module has 249 references showing active DRM client usage. GPU is at 35°C with 17W / 184W TDP at idle, 3% utilization.

For best Wayland app compatibility, set env vars in shell config:
```
export GBM_BACKEND=nvidia-drm
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export QT_QPA_PLATFORM=wayland
```

## References
- [[nvidia-wayland-kwin-latency-policy]]
- [[manjaro-system-specs-arrow-lake]]
