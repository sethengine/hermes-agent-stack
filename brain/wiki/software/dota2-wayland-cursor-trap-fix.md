---
source_session: 20260608_001440_375423
date: 2026-07-05
category: software
tags: [dota2, wayland, cursor, gaming, proton, sdl]
---

# Dota 2 Wayland Cursor Trap Fix

Dota 2 on Wayland has a bug where the cursor gets trapped/grabbed by the game window and won't release on alt-tab, making the desktop cursor non-interactive.

## Quick Fix (in-game console)

```
engine_no_focus_sleep 0
dota_use_desktop_cursor 1
```

## Permanent Fix

Add to Steam launch options to force SDL to use XWayland instead of native Wayland:

```
SDL_VIDEODRIVER=x11 gamemoderun %command%
```

## Root Cause

Dota 2's native Wayland cursor confinement (grab) doesn't release properly on alt-tab. Forcing SDL to X11 via XWayland avoids the cursor trap entirely with zero performance impact.

> ⚠️ **Opposite symptom:** If your cursor becomes *non-interactive in-game* (not trapped on alt-tab, but unusable during gameplay), see [[dota2-xwayland-cursor-capture-loss]] — the root cause is the XWayland bridge decaying, and the fix is `SDL_VIDEO_DRIVER=wayland`.

[[wayland-gaming-issues]]
[[proton-game-tweaks]]
[[nvidia-wayland-kwin-latency-policy]]
