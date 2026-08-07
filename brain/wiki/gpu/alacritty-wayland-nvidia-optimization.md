---
session: 20260502_174824_f53a50
date: 2026-05-02
category: gpu
tags: [alacritty, terminal, wayland, nvidia, text-clipping, lag]
---

# Alacritty Wayland + NVIDIA Optimization

On NVIDIA Wayland (driver 590.48.01), Alacritty exhibited text clipping/delay when typing fast. The optimized config in `~/.config/alacritty/alacritty.toml`:

```toml
[window]
dynamic_padding = false
decorations = "None"

[font]
size = 12.0

[scrolling]
multiplier = 3
```

Also recommended: disable KWin compositor effects for Alacritty via Window Rules (System Settings → Window Management → Window Rules → Add "alacritty" → Compositing: "Force off").

Environment variables for app Wayland-native rendering:
```
export GBM_BACKEND=nvidia-drm
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export QT_QPA_PLATFORM=wayland
```

## References
- [[nvidia-wayland-kwin-latency-policy]]
- [[corsair-katar-pro-xt-config]]
