---
source_session: 20260709_193718_2e6307
category: system
tags: [kwin, environment-vars, systemd, session, kwin_drm_override_safety_margin]
date: 2026-07-09
---

# KWin Environment Variables via systemd — Session Reload

KWin environment variables set via `~/.config/environment.d/99-kwin.conf` are only loaded at session start by systemd user services. Changes to these files after the session has started do NOT affect the running KWin process.

## Problem

Adding or modifying a file like:

```
~/.config/environment.d/99-kwin.conf
  KWIN_DRM_OVERRIDE_SAFETY_MARGIN=0
```

...after the Plasma session began means KWin never sees the variable. Checking `/proc/$(pidof kwin_wayland)/environ` confirms it's absent.

## Fix — Reload Without Full Logout

```bash
# Import current environment to systemd user bus
systemctl --user import-environment
# Restart KWin only
systemctl --user restart plasma-kwin_wayland.service
```

This applies the environment.d changes without restarting the entire session. Confirmed to work for `KWIN_DRM_OVERRIDE_SAFETY_MARGIN` and other KWin environment variables.

## Related

- [[kwin-safety-margin-restore]]
- [[nvidia-wayland-vrr-input-lag-kwin]] — another KWin setting that requires restart
