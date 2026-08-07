# MangoHud FPS Limiting for Proton Games

**Source Session:** `20260706_194614_c828c3` (Diablo 2 Wayland Nvidia Settings)
**Date:** 2026-07-08
**Category:** software

## Problem

Game built-in frame limiters (e.g. Diablo 2 Resurrected) are broken under Proton/Wayland. DXVK/VKD3D translates DirectX presentation timing (`IDXGISwapChain::Present`) to Vulkan, but Wayland's presentation queue doesn't honor the game's requested intervals. The game *thinks* it's limiting but the driver ignores it.

## Fix

[[mangohud]] hooks at the Vulkan layer, below the broken DX limiter. Minimal D2R config (`~/.config/MangoHud/diablo_ii_resurrected.conf`):
```
fps_limit=60
no_display=1
fps_limit_method=early
vsync=2
```
Launch option: `mangohud %command%`

## Per-app Config

MangoHud matches executable name. For Steam/Proton games where the match may fail, use env var:
```
MANGOHUD_CONFIG="fps_limit=60,no_display=1" mangohud %command%
```

## Gamescope Alternative

`gamescope -f -r 60 -- mangohud %command%` creates a micro-compositor with hardware-level frame cap that can't be bypassed. Also fixes fullscreen/resolution issues.

## Key Options

| Option | Purpose |
|--------|---------|
| `fps_limit=N` | Cap FPS; `0`=uncapped; comma list for toggle cycling |
| `fps_limit_method=early` | Sleep before present (smoother) |
| `fps_limit_method=late` | Sleep after (lower latency, may stutter) |
| `no_display=1` | Hide HUD, keep cap active |
| `vsync=2` | Mailbox mode (tear-free, low latency) |
