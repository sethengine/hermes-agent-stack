---
source: 20260706_194614_c828c3
category: software
date: 2026-07-06
tags: [diablo-2, proton, nvidia, wayland, proton-ge, dxvk, community-research]
---

# D2R: Community-Validated Proton Fixes (NVIDIA Wayland)

Last30Days research across 14 Reddit threads and ProtonDB confirms community patterns:

## Most reliable: GE-Proton10-34 or Proton Experimental

RTX 3080 (CachyOS, Proton 11.0 beta), RTX 4070 (NVIDIA 595), and RTX 4070 Ti (EndeavourOS, NVIDIA 580) all report fullscreen fixes with GE-Proton. Stock Proton 10 breaks fullscreen on all.

## Windowed mode crash workaround

RTX 3060 Ti (Pop!_OS, Proton Experimental, driver 535.86.05): "game crashes at random times in full-screen, windowed mode solves it." Multiple RTX 3070 Ti users (NVIDIA 590) report frequent crashes (5-60 min intervals) across distros.

## Alt+Enter as universal band-aid

Fixes 1/4-screen render bug and stuck-in-fixed-window: Alt+Enter → windowed, Alt+Enter → fullscreen.

## References
- [[diablo-2-resurrected-proton-nvidia-wayland]]
- [[proton-ge-nvidia-wayland-fullscreen]]
- [[linux-gaming-frame-limiters]]
