---
source: 20260706_194614_c828c3
category: software
date: 2026-07-06
tags: [proton, ge-proton, nvidia, wayland, fullscreen, gaming, steam, dxvk]
---

# Proton GE Fixes Fullscreen on NVIDIA Wayland

Stock Proton 10 has a persistent fullscreen/resolution bug on NVIDIA + Wayland across multiple games and distros. GE-Proton consistently fixes it.

## Pattern (community-validated across CachyOS, Pop!_OS, EndeavourOS, Manjaro)

- Stock Proton 10: stuck in fixed window, no resolution options, fullscreen reverts to windowed
- GE-Proton10-34 or Proton Experimental: resolves it for RTX 3080, 4070, 4070 Ti on NVIDIA 595/580
- `PROTON_ENABLE_WAYLAND=0` launch option as fallback when GE-Proton isn't sufficient

## Driver family compatibility

NVIDIA 590/595 driver branches work well with Proton 10.0-3 and GE-Proton on RTX 5070 Ti (Fedora), RTX 5080 (CachyOS) — both report flawless behavior.

## References

- [[diablo-2-resurrected-proton-nvidia-wayland]]
- [[linux-gaming-frame-limiters]]
- [[gamescope-hdr-kde-wayland-nvidia]]
