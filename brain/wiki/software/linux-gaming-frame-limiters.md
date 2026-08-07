---
source: 20260706_194614_c828c3
category: software
date: 2026-07-06
tags: [framerate, fps-limit, mangohud, gamescope, dxvk, proton, vulkan]
---

# Linux Gaming Frame Limiters

When in-game frame limiters don't work through DXVK/VKD3D under Wayland, use external limiters.

## MangoHud (most reliable)
```
# ~/.config/MangoHud/MangoHud.conf
fps_limit=60
no_display=1
```
Launch: `mangohud %command%`
Hooks at Vulkan layer — works regardless of game API.

## Gamescope (compositor wrapper)
```
gamescope -f -r 60 -- %command%
```
Creates micro-compositor hard-capped at target FPS. Also fixes fullscreen/resolution issues.

## DXVK config
```
# dxvk.conf in proton prefix
dxvk.enableAsync = False
dxvk.numCompilerThreads = 2
```
Less reliable than MangoHud for frame limiting.

## References
- [[diablo-2-resurrected-proton-nvidia-wayland]]
- [[gamescope-hdr-kde-wayland-nvidia]]
