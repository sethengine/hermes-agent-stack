# Lighter High-Contrast KDE Plasma 6 Themes

Research findings from `last30days` and web searches on lighter KDE themes with high contrast text (not pure white).

## Theme Catalog

### Relax-Light-Plasma (by L4ki — already in AUR/manual install)

- **Author:** L4ki (same developer as Slot-Plasma-Themes)
- **Type:** Plasma Style (desktoptheme)
- **Window background:** RGB 239,240,241 — warm off-white/light gray (NOT pure white)
- **View background:** RGB 252,252,252 — very light but still off-white
- **Text color:** RGB 35,38,39 — near-black, excellent readability
- **Available in:** AUR (as part of relax-plasma-themes), KDE Store, GitHub
- **Ships with:** dedicated colors file, translucent/solid variants, weather widgets
- **Pair with:** BreathLight or OxygenCold colorscheme for max text contrast

This is the ideal match for "light but not white" — the Window background is a warm textured gray (avg luminance 240) rather than blinding 255,255,255.

### Installed Theme Text Contrast Reference

When evaluating already-installed themes on a typical Arch/Manjaro KDE Plasma 6 system, these are the actual [Colors:View] text contrast values found:

| Theme/Scheme | Background | Text | Readability |
|---|---|---|---|
| Relax-Light-Plasma | 252,252,252 (near-white) | 35,38,39 (near-black) | Excellent |
| 101610-Gentle | 237,237,238 (warm gray) | 0,0,0 (pure black) | Maximum |
| BreathLight | 255,255,255 | 35,38,41 | Very good |
| BreezeLight | 255,255,255 | 35,38,41 | Very good |
| OxygenCold | 255,255,255 | 20,19,18 (near-black) | Excellent |
| LayanLight | 255,255,255 | 51,51,51 (gray) | Medium — gray text |
| ElementaryLuna | 255,255,255 | 77,77,77 | Low — washed out |

The key metric: ForegroundNormal values below 40 produce sharp text. Values above 50 appear gray/washed out.

### Utterly Nord Light / Utterly Nord Light Solid

- **KDE Store:** [Utterly Nord Light Solid](https://store.kde.org/p/2151938), [Utterly Nord Light](https://store.kde.org/p/2151940)
- **GitHub:** [HimDek/Utterly-Nord-Plasma](https://github.com/HimDek/Utterly-Nord-Plasma)
- **Type:** Global Theme (Plasma 6)
- **Palette:** Nord light (cool grays, soft blues — not white)
- **Features:** Tela Circle Nord icons, rounded edges, Material You clock widget
- **Solid vs Original:** "Solid" avoids transparency issues that reduce text readability
- **Color scheme file:** `UtterlyNordLight.colors` in the GitHub repo — can be edited directly
- **YouTube:** "Easy KDE Plasma 6 Customization | Solid Light" (youtube.com/watch?v=_ntY6yqPQts)

### KDE Air Theme (Revived in Plasma 6.7)

- **Source:** Built into Plasma 6.7 (June 2026 release)
- **History:** Originally KDE 4's default theme; removed in Plasma 6; revived by Filip Fila, Nuno Pinheiro, and Marco Martin
- **Look:** Soft light with widget transparency and blur effect behind windows
- **Contrast:** Blur adds depth without washing out readability
- **Coverage:** [9to5Linux](https://9to5linux.com/kde-4s-air-theme-making-a-comeback-oxygen-gets-major-revamp-for-plasma-6-7), [It's FOSS News](https://itsfoss.com/news/kde-plasma-oxygen-air-comeback/)

### Oxygen Theme (Revived in Plasma 6.7)

- **Source:** Built into Plasma 6.7
- **Look:** Dark tones with glassy aesthetic (opposite of Air — use for dark variant)
- **History:** Default KDE 4 theme, got major revamp for Plasma 6.7

### Slot-Plasma-Themes (by L4ki)

- **Source:** [Bright Coding blog](https://blog.brightcoding.dev/2026/04/30/slot-plasma-themes-the-revolutionary-theme-pack-transforming-kde-desktops)
- **Type:** Complete theme suite (Plasma + GTK + icons)
- **Variants:** 8+ color variants — from deep charcoal to lighter minimal variants
- **Architecture:** JSON-based palette system, custom SVG shadow definitions
- **Performance:** Reduces KWin compositor overhead by ~15% vs heavier themes
- **Coverage:** GTK 2/3/4 for non-Qt apps (Dolphin, Firefox, GIMP, VS Code)
- **Icon pack:** 48+ application categories

### Klassy

- **Source:** [github.com/paulmcauley/klassy](https://github.com/paulmcauley/klassy)
- **Type:** Application Style + Global Theme (Kvantum-based)
- **Components:** Window decoration, application style, color scheme, plasma style, icons
- **Highlight:** "Arguably the best scrollbars on any platform" per community
- **Customization:** Highly configurable theme engine

## Customization Techniques

### Frame Contrast (Plasma 6.6+)

- **Developer:** Akseli Lahtinen (akselmo.dev)
- **Blog:** https://akselmo.dev/posts/frame-contrast-settings/
- **Location:** System Settings > Appearance > Application Style > Breeze > Fine Tuning
- **Slider:** 0 (none) to 100 (maximum contrast)
- **Scope:** QtQuick, QtWidgets/Breeze, Plasma SVG (all use `class: ColorScheme-Frame`)
- **Before 6.6:** The slider existed but did nothing in Breeze style (leftover from Oxygen)

### Text Contrast (Not Frame Contrast)

**Important distinction:** KDE Plasma 6.6+ has a "Frame Contrast" slider in Breeze Fine Tuning that affects **window frame/button outline contrast**, NOT text readability. When a user asks for better text readability, they need color scheme editing (below), not the frame contrast slider.

### Custom Color Schemes

- **Location:** `~/.local/share/color-schemes/`
- **Format:** INI
- **Key values for contrast:**
  ```ini
  [Colors:View]
  ForegroundNormal=R,G,B     # Text color
  BackgroundNormal=R,G,B     # Background color
  [Colors:Window]
  ForegroundNormal=R,G,B
  BackgroundNormal=R,G,B
  ```
- **High-contrast-ish approach:** Dark gray backgrounds + vibrant text colors (not pure black/white) — per KDE Discuss user
- **ForegroundNormal tip:** Change default `49,54,59` to `144,144,144` for readability on mixed backgrounds — per r/kde
- **KDE Discuss source:** https://discuss.kde.org/t/my-high-contrast-ish-colorschemes/1670

### Web Searches for Lighter Theme Research

When using last30days or web search to research this topic, use these queries:
- `KDE Plasma light theme not white high contrast`
- `KDE Plasma 6 Utterly Nord Light customization`
- `KDE Plasma color scheme edit ForegroundNormal`
- `best KDE Plasma light theme high contrast 2025 2026`
- `KDE Plasma theme customization high contrast readability`

Note: last30days engine returns thin results for this niche query (11 Reddit items). Supplement heavily with web searches (SearXNG/Brave).

## Reddit Threads of Interest

- r/kde "Light theme recommendations" — https://www.reddit.com/r/kde/comments/1dspiin/
- r/kde "KDE Theme for Best Accessibility/High Contrast" — https://www.reddit.com/r/kde/comments/15x6yx8/
- r/kde "Good Light KDE Plasma Theme?" — https://www.reddit.com/r/kde/comments/12zq0am/
- r/kde "How do I change the color of text in a Plasma desktop theme?" — https://www.reddit.com/r/kde/comments/gez0yh/
- r/kde "Plasma 6.7" (982pts) — https://www.reddit.com/r/kde/comments/1u8rj3v/
