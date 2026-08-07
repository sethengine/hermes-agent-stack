---
source: "20260710_212706_69a41c"
date: "2026-07-10T19:06:43+00:00"
category: "gpu"
related: ["gamescope-hdr-kde-wayland-nvidia", "vulkan-present-modes", "nvidia-595-grub-modprobe-env-kwin-config"]
---

# Gamescope + Proton 11 + NVIDIA 595: Diablo 2 Resurrected Config

D2R-specific Gamescope/HDR config for RTX 5060 Ti, NVIDIA 595, and GE-Proton11-1 on KDE Wayland.

## Gamescope Launch Options

```
gamescope -W 2560 -H 1440 -r 165 --hdr-enabled --hdr-itm-enable --hdr-sdr-content-nits 400 --adaptive-sync --immediate-flips -f -- %command%
```

`--hdr-itm-enable` inverse-tone-maps SDR content to HDR output (D2R is SDR natively). `--hdr-sdr-content-nits 400` is the sweet spot for D2R's dark aesthetic. `--immediate-flips` skips the pending-flip queue on NVIDIA, avoiding 1-frame hold.

## Proton 11 Env Vars

```
DXVK_HDR=1                             # enable HDR in VKD3D-Proton
PROTON_ENABLE_NVAPI=1                  # DLSS, Reflex via NVAPI
VKD3D_CONFIG=dxr11,force_static_cbv   # D3D12 config
DXVK_ASYNC=1                           # async shader compilation
SKIP_LAUNCHER=1                        # known bug: Gamescope + D2R launcher
```

## Known Bug

D2R launcher spawns tiny and unresponsive inside Gamescope. Workaround: `SKIP_LAUNCHER=1` env var before gamescope, or use protontricks to add it.

References: [[gamescope-hdr-kde-wayland-nvidia]], [[nvidia-595-grub-modprobe-env-kwin-config]]
