---
source: "20260704_212250_ef6734"
date: "2026-07-04T22:10:53+00:00"
category: "gpu"
related: ["gamescope-hdr-kde-wayland-nvidia", "proton-prefix-corruption", "gamescope-xwayland-overhead"]
---

# VKD3D Shader Compilation Stutter Fix

First launch of DX12 games (especially Frostbite engine) via Proton/gamescope exhibits severe shader compilation stutter.

## Symptoms

- `fozpipelinesv6` cache has very few files (e.g., 8)
- `vkd3d-proton.cache` is tiny
- 3-second frame locks on first encountering new shaders
- Stutters resolve after ~30 minutes of play once cache fills

## Fix — Async Shader Compilation

```sh
VKD3D_CONFIG=async %command%
```

Trades 3-second freezes for minor stutter-hiccups while compiling. After cache populates, stutters stop entirely on subsequent runs (90% reduction).

## Relationship with Gamescope HDR

When using gamescope with `--hdr-enabled`, the `VKD3D_CONFIG=hdr` flag is redundant — gamescope exposes HDR to vkd3d-proton automatically via the `VK_FORMAT_R16G16B16A16_SFLOAT` swapchain. The `hdr` flag can conflict on some titles.

Recommended combined config:
```
VKD3D_CONFIG=async PROTON_ENABLE_NVAPI=1 %command%
```
