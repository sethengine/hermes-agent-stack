# Session Reference: HP X34 (3440×1440) Font Tuning

**Date**: 2026-07-25
**System**: Manjaro / KDE Wayland / NVIDIA 595.71 / RTX 5060 Ti

## Initial State

| Check | Before | After |
|-------|--------|-------|
| GTK antialiasing | `grayscale` | `rgba` |
| GTK hinting | `slight` | `slight` (unchanged) |
| KDE XftHintStyle | `hintmedium` | `hintslight` |
| KDE DPI | unset (96) | 110 |
| Xft.dpi | 96 | 110 |
| Sub-pixel symlink | missing | needs sudo |
| `FREETYPE_PROPERTIES` | unset | v40 + stem darkening |
| fonts.conf conflicts | `hintslight` then `hintmedium` | clean, only `hintslight` |

## Files Created/Modified

- **`~/.config/fontconfig/fonts.conf`** — cleaned, hintmedium removed, lcdlight added
- **`~/.config/environment.d/99-font-rendering.conf`** — new file with FREETYPE_PROPERTIES
- **`~/.Xresources`** — new file with correct DPI + rendering settings
- **`~/.config/kdeglobals`** — XftHintStyle → hintslight, XftDpi → 110
- **`~/.config/kcminputrc`** — forceFontDPI → 110

## DPI Math

3440² + 1440² = 11,833,600 + 2,073,600 = 13,907,200
√13,907,200 ≈ 3,729 px diagonal
3,729 / 34" = **109.6 → 110 DPI**

## Pending

```bash
sudo ln -sf /usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf /etc/fonts/conf.d/
```
