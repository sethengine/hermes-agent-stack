---
source_session: 20260607_182305_b96905
source_date: 2026-07-05
category: software
related: [kde-plasma-light-theme-contrast, kwin-background-contrast, kwriteconfig5-usage]
tags: [kde, plasma-6, text-rendering, accessibility, desktop-icons, wayland]
---

# KDE Plasma 6 Desktop Text Readability Settings

## Desktop Icon Text Outline/Contour

Plasma 6 has a built-in text shadow/outline setting for desktop icon labels, controlled by `textShadow`:

- **0** = No shadow (default)
- **1** = Drop shadow behind text
- **2** = Outline/contour around text characters
- **3** = Both shadow and outline

**GUI:** Right-click desktop > Configure Desktop > Icons > three-dot menu > Configure Folder View > Appearance > Text shadow dropdown

**Command:** `kwriteconfig5 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc --group Containments --group 2 --group General --key textShadow 2`

**Note:** Use `--key textShadow 2` syntax (no `--value` flag) — just the number at the end.

## KWin Background Contrast (Wayland Limitation)

The `Effect-BackgroundContrast` KWin effect provides a darkened semi-transparent region behind panels, tooltips, and popups for text readability. **Not available on Wayland** — it only exists in `kwin-x11`. On Plasma 6.6.5 Wayland, config writes are silently ignored.

## Breeze Frame Contrast

Controls how bold frame outlines appear around windows. System Settings > Appearance > Application Style > Breeze > Fine Tuning. Range 0-100. Command: `kwriteconfig5 --file ~/.config/breezerc --group Common --key FrameContrast --value 40`.

## Font Hinting

Plasma 6 defaults to `hintslight`. Bumping to `hintmedium` or `hintfull` sharpens text on light backgrounds. Set via `~/.config/kdeglobals` under `[General]` with `XftHintStyle=hintfull`.
