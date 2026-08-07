---
source: "20260704_212250_ef6734"
date: "2026-07-04T22:10:53+00:00"
category: "gpu"
related: ["gamescope-hdr-kde-wayland-nvidia", "vkd3d-shader-compilation-stutter"]
---

# Gamescope XWayland Overhead and Stutter

On KDE Wayland with NVIDIA, gamescope goes through XWayland for the game window by default, introducing extra copy + sync latency.

## Root Cause

- `vk_xwayland_wait_ready` causes Vulkan to wait on XWayland before each frame
- VRR may not engage properly through the XWayland chain
- Results in microstutter that is absent on Windows

## Fix — `--expose-wayland`

Makes gamescope present directly to KWin's Wayland surface:

```
gamescope ... --expose-wayland --steam -- env PROTON_ENABLE_NVAPI=1 %command%
```

Removes the `vk_xwayland_wait_ready` bottleneck.

## Alternative — Skip Gamescope Entirely

Drop the gamescope wrapper for direct Proton + KWin Wayland:

```
PROTON_ENABLE_NVAPI=1 PROTON_HIDE_NVIDIA_GPU=0 VKD3D_CONFIG=async %command%
```

Requires desktop HDR to be enabled first for HDR output:
```sh
kscreen-doctor output.DP-3.hdr.enable
```

## VRR Verification

Check VRR status while game is running:
```sh
cat /sys/class/drm/card0-DP-3/vrr_capable  # 1 = capable
cat /sys/class/drm/card0-DP-3/vrr_enabled   # 1 = actually active
```

Without VRR engaging at 165Hz, frame time variance is perceived as stutter.
