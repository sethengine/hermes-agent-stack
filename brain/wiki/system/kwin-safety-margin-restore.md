---
source_session: "20260709_193718_2e6307"
date: "2026-07-09"
category: system
related: [kwin, wayland, environment-d]
---

# KWin DRM Safety Margin Restore

The `KWIN_DRM_OVERRIDE_SAFETY_MARGIN` variable in `~/.config/environment.d/99-kwin.conf` controls KWin's DRM buffer safety margin. A negative value (e.g., `-100`) reduces it below KWin's calculated safe region; `0` uses KWin's default computation.

Changed from `-100` to `0` to restore normal margins. Requires KWin restart (`kwin_wayland --replace` or logout/login) to take effect.

Notable: the config file had the value at `-100` not `-150` as the user believed. Also check `99-kwin-latency.conf` for overlapping KWin env vars.

[[wayland-tweaking]] [[kwin-performance]]
