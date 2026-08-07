---
source_session: 20260731_191512_a88c93
category: system
date: 2026-07-31
tags: [kwin, kwin_compose, compositor, wayland, environment, login-loop]
---

# KWIN_COMPOSE Accepted Values + Env Landmine

## Accepted values (KWin 6.7.3, verified from source)

`KWIN_COMPOSE` is read once at compositor start via `qgetenv()` in `attemptOpenGLCompositing()` (compositor.cpp). Only exact matches `O2` / `O2ES` are accepted. Any other value (e.g. bare `O`) makes the compositor log `Could not fulfill the requested compositing mode in KWIN_COMPOSE` and **quit → Wayland session won't start** (black screen / login loop). Historical `X` (XRender) and `N` were removed by Plasma 5.27.

## ⚠️ Landmine — duplicate env scripts conflict

`~/.config/plasma-workspace/env/*.sh` are sourced in lexicographic order; **last wins**. On this system:

| File | Value |
|---|---|
| `kwin-opengl.sh` | `export KWIN_COMPOSE=O2ES` ✅ |
| `kwin.sh` (line 6) | `export KWIN_COMPOSE=O` ❌ invalid |

`kwin.sh` runs last → `O` wins at next login → compositor quits. Current session still shows O2ES only because it started before the edit. **Fix: correct line 6 of kwin.sh to `O2ES` or delete it.**

## Why changes need relog

- D-Bus `/Compositor reinitialize` re-reads the running process's env — unmodifiable from outside (`/proc/PID/environ` read-only) → zero effect.
- `kwin_wayland --replace` on Wayland just signals the old instance; systemd restarts it with the **systemd user env** (`systemctl --user set-environment KWIN_COMPOSE=...` first, but that kills the session anyway).
- Only reliable paths: relog/reboot, or `systemctl --user set-environment` + session restart.

## Related

- [[kwin-systemd-environment-vars]]
- [[kwin-safety-margin-restore]]
