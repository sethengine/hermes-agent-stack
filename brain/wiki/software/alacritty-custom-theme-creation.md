---
source_session: 20260601_164712_ab05bd
extracted_date: 2026-07-17
category: software-development
tags: [alacritty, themes, toml, color-schemes]
---

# Creating Custom Alacritty Themes

Alacritty themes are TOML files with `[colors]` sections for `primary`, `normal`, `bright`, `cursor`, and `selection`. Custom themes go in `~/.config/alacritty/themes/themes/`.

## Theme patterns built

| File | Background | Style |
|------|-----------|-------|
| `low_contrast.toml` | `#333333` dark gray | Muted accents, readable fg |
| `low_contrast_bright.toml` | `#333333` dark gray | GitHub Dark palette with brighter foreground |
| `concrete.toml` | `#9a9a9a` medium gray | Low saturation, near-black text |
| `pumice.toml` | `#b4b4b4` light gray | Muted, readable |
| `cursor_dim.toml` | `#1e1e28` | Cursor palette with lighter bg |

## Key structure

```toml
[colors.primary]
background = "#333333"
foreground = "#eeeeee"

[colors.normal]
black = "#1c2128"
red = "#f06060"
green = "#4ac068"
yellow = "#e0c040"
blue = "#4090f0"
magenta = "#c080e0"
cyan = "#40d0c0"
white = "#e0e0e0"

[colors.bright]
# ... brighter variants
```

The `import = ["~/.config/alacritty/themes/themes/YOUR_THEME.toml"]` line in `alacritty.toml` activates it. [[alacritty-theme-switcher-fzf]] can browse and apply instantly via live reload.

See [[opencode-theme-creation]] for porting these palettes to OpenCode.
