---
source_session: 20260607_182305_b96905
source_date: 2026-07-05
category: software
related: [kde-plasma-desktop-text-readability, kwriteconfig5-usage, relax-light-plasma]
tags: [kde, plasma-6, themes, light-themes, contrast, accessibility]
---

# KDE Plasma 6 Light Theme Contrast

On Manjaro Plasma 6.6.5, these light themes are available with good text contrast:

## Already Installed Light Schemes (ranked)

| Scheme | Background | Text | Notes |
|--------|-----------|------|-------|
| **101610-Gentle** | 237,237,238 off-white | 0,0,0 near-black | Maximum contrast, non-blinding |
| OxygenCold | 255,255,255 | 20,19,18 | High contrast |
| BreathLight | 255,255,255 | 35,38,41 | High contrast |
| LayanLight | 255,255,255 | 51,51,51 | Medium (grayish text) |

## Relax-Light-Plasma (Best Light Plasma Style)

Already installed from L4ki. Window background RGB 239,240,241 (warm gray, not white). View area RGB 252,252,252 (soft off-white). Text RGB 35,38,39 (near-black). Apply via System Settings > Appearance > Plasma Styles.

## Editing Color Scheme Contrast

Edit `ForegroundNormal=` in any `.colors` file under `~/.local/share/color-schemes/`. Lower RGB values = darker text = more contrast. For LayanLight: changing `ForegroundNormal=51,51,51` to `20,20,20` sharpens readability while keeping text non-harsh.

## Utterly Nord Light (AUR)

Available via `yay -S utterly-nord-plasma`. Cool-toned light grays (Nord palette). Use Solid variant to avoid transparency washout.
