---
source_session: 20260716_180611_2e4ebc
date: 2026-07-16
category: gpu
tags: [nvidia, kwin, cursor, wayland, 595]
---

# NVIDIA 595 KWin Invisible Cursor on Wayland

The NVIDIA 595 Beta driver (595.71.05) can cause the mouse cursor to become invisible on KDE Wayland while the cursor still functions (click targets work).

## Fixes

1. **`KWIN_FORCE_SW_CURSOR=1`** — Forces KWin to use software cursor rendering, bypassing NVIDIA's hardware cursor plane. Set in `~/.config/environment.d/kwin_sw_cursor.conf` or via systemd `environment.d`.
2. **Switch to standard cursor theme** — Non-standard themes like `pixelfun3` lack proper Wayland cursor assets. Breeze, Breeze_Light, or Adwaita work reliably.
3. **Apply via Plasma env sourcing** — `~/.config/plasma-workspace/env/` is more reliable than systemd for KWin env vars.

## KWin Restart Black Screen (Wayland)

Restarting KWin on Wayland via `systemctl restart plasma-kwin_wayland.service` collapses the entire graphical session:

1. KWin stops → compositor dies → screen goes black
2. `PartOf=graphical-session.target` cascades → all session services stop
3. NVIDIA 595 fails to re-init the display pipeline → SDDM greeter can't start → **stays black forever**

This is a regression in NVIDIA 595 Beta. The only recovery is a hard reboot.

[[nvidia-wayland-kwin-crash]] [[kwin-force-software-cursor]] [[nvidia-595-beta]]
