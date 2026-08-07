---
source_session: 20260712_194955_d06bd6
date: 2026-07-14
category: software
tags: [dota2, wayland, xwayland, cursor, capture-loss, sdl, nvidia, kde, pointer-confinement]
---

# Dota 2 XWayland Cursor Capture Loss on KDE Wayland + NVIDIA

## Problem

In Dota 2 on KDE Wayland with NVIDIA, the in-game cursor **becomes the KDE desktop cursor and is non-interactive** (cannot click UI, drag, or aim). The game window holds focus but won't accept mouse input. Alt-tabbing temporarily fixes it but the issue returns.

## Root Cause

**Dota 2's launcher (`dota.sh`, lines 76–84) explicitly forces `SDL_VIDEO_DRIVER=x11`** on Linux, even on Wayland sessions. Valve's comment:

> *"There is Wayland support in SDL but a recent (5/23/2025) attempt at allowing SDL to default to Wayland caused a number of customer issues so keep the default at X11 for now."*

This forces the game through **XWayland**. Cursor confinement goes through a fragile **3-layer bridge**: SDL → X11 → XWayland → `zwp_pointer_constraints_v1` (Wayland protocol). This bridge decays over time, especially on:
- Alt-tab / focus-change events (XWayland surface loses pointer lock)
- Extended play sessions (KWin compositor events trigger constraint re-evaluation)
- KDE Plasma panels or notifications stealing focus

## Fix — Force Native Wayland SDL

The most reliable fix is to bypass XWayland entirely by having SDL use Wayland natively:

```
SDL_VIDEO_DRIVER=wayland %command% -fullscreen -window_mode exclusive
```

If multi-monitor display index is wrong, add `-sdl_displayindex N` (0, 1, or 2).

## Harden X11 Path (Fallback)

If Wayland SDL causes issues (crashes, black screen), harden the XWayland path:

```
SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0 SDL_MOUSE_FOCUS_CLICKTHROUGH=1 %command% -fullscreen -window_mode exclusive dota_mouse_window_lock 1
```

## Notes

- **Distinct from cursor trap:** This is the *opposite* symptom of [[dota2-wayland-cursor-trap-fix]] (which covers cursor not releasing on alt-tab — fix: `SDL_VIDEODRIVER=x11`). Here, the cursor is *lost in-game* and the fix is `SDL_VIDEO_DRIVER=wayland`.
- Gamescope `--force-grab-cursor` causes black screen on NVIDIA (untested on RTX 5060 Ti / 570+ drivers).
- No root-cause fix from Valve is committed as of 2026-07-14 (`dota.sh` still forces x11).

## References

- ValveSoftware/Dota-2 Issue #2612 — borderless window cursor lock
- ValveSoftware/Dota-2 Issue #2705 — multi-monitor mouse capture
- Steam Community — Mouse stuck in games on Wayland
- Arch BBS — Games using Proton fail to capture mouse on Plasma 6 Wayland
- SDL CaptureMouse issue #14974
- GameTracking-Dota2 `dota.sh`

[[wayland-gaming-issues]]
[[steam-nvidia-wayland-rendering]]
[[gamescope-xwayland-overhead]]
[[kwin-latency-document]]
[[nvidia-wayland-hardware-cursors]]
