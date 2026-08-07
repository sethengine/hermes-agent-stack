# Wallpapers and Setup Notes for Lighter KDE Plasma 6 Themes on Manjaro

Found during a session researching lighter (not white, high-contrast text) KDE Plasma 6 themes on Manjaro.

## Installed Light Themes Already Available

System: Manjaro KDE Plasma 6.6.5 (Wayland)

### Plasma Styles (already in ~/.local/share/plasma/desktoptheme/)

Relax-Light-Plasma (by L4ki) is the best match for "light but not white":
- Window bg: RGB 239,240,241 (warm off-white / light gray)
- View bg: RGB 252,252,252 (very light, near-white)
- Text fg: RGB 35,38,39 (near-black for excellent readability)
- Has solid/ translucent/ and weather/ subdirectories
- Author: L4ki (same developer as Slot-Plasma-Themes)

Other installed themes that are NOT light (dark/colored):
- Gently, Infinity-Plasma, Layan, Nordic* -- all dark themes
- ChromeOsKDE -- uses system colorscheme (no own colors file)

### Color Schemes (already in ~/.local/share/color-schemes/)

Ranked by text contrast (ForegroundNormal on light background):

| Scheme | View bg | View fg | Text Readability |
|--------|---------|---------|------------------|
| 101610-Gentle | 237,237,238 | 0,0,0 | Maximum (dark off-white + pure black) |
| OxygenCold | 255,255,255 | 20,19,18 | Excellent |
| Oxygen | 255,255,255 | 31,28,27 | Excellent |
| BreathLight | 255,255,255 | 35,38,41 | Very good |
| BreezeLight | 255,255,255 | 35,38,41 | Very good |
| LayanLight | 255,255,255 | 51,51,51 | Grayish text -- suboptimal |
| ElementaryLuna | 255,255,255 | 77,77,77 | Low -- washed out |

Rule of thumb: ForegroundNormal values < 40 produce sharp text. Values > 50 appear gray/washed out.

## KWin Effects -- Wayland vs X11

Background Contrast effect (which adds darkened semi-transparent regions behind panels/tooltips for readability) is X11-only. On Wayland:

- Effect files live under `/usr/share/kwin-x11/effects/` and `/usr/share/kwin-x11/builtin-effects/`
- Wayland loads from `/usr/share/kwin/effects/` (only `cube` on this system)
- Writing to `~/.config/kwinrc [Effect-BackgroundContrast]` is silently ignored on Wayland

## Desktop Icon Text Shadow/Outline

Setting `textShadow` on the desktop folder view adds text contours to icon labels:

```bash
kwriteconfig5 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
  --group Containments --group 2 --group General --key textShadow 2
```

Values: 0=none, 1=shadow, 2=outline, 3=both

GUI path: Right-click desktop > Configure Desktop > Icons > three-dot menu > Configure Folder View > Appearance > Text shadow

## Note on kwriteconfig5 Syntax

The tool takes the value as a positional argument, not a `--value` flag:

```bash
# Correct:
kwriteconfig5 --file x --group g --key k value

# Wrong (errors with "Unknown option 'value'"):
kwriteconfig5 --file x --group g --key k --value value
```
