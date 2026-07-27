---
name: linux-font-rendering
description: >-
  Diagnose and configure system-wide font rendering on Linux (Manjaro/Arch).
  Covers fontconfig, GTK, Qt/KDE, Freetype env vars, and XWayland — ensuring
  subpixel RGB rendering, proper hinting, LCD filtering, and DPI everywhere.
tags:
  - linux
  - fonts
  - fontconfig
  - freetype
  - rendering
  - gtk
  - kde
  - qt
  - wayland
---

# Linux Font Rendering

Diagnose and improve font rendering quality system-wide — all toolkits (GTK, Qt/KDE, native Freetype), all display stacks (Wayland native, XWayland).

## Layers Overview

Font rendering on Linux involves **five independent layers**. A fix in one does not affect the others:

| Layer | Config mechanism | Affects |
|-------|-----------------|---------|
| **Fontconfig** | `~/.config/fontconfig/fonts.conf` + `/etc/fonts/conf.d/` symlinks | All fontconfig-aware apps (most toolkits) |
| **GTK** | `gsettings` under `org.gnome.desktop.interface` | GTK apps (Firefox, Chrome, Thunar, GIMP) |
| **Qt / KDE** | `kdeglobals` / `kcminputrc` / `kwriteconfig5` | Qt/KDE apps (plasmashell, Dolphin, Kate, etc.) |
| **Freetype** | `FREETYPE_PROPERTIES` env var | All apps using libfreetype (everything) |
| **XWayland** | `~/.Xresources` | XWayland-backed X11 apps |

## Diagnostic Procedure

### 1. Check Freetype build

```bash
# Freetype version
pkg-config --modversion freetype2

# Subpixel rendering enabled?
grep -i 'FT_CONFIG_OPTION_SUBPIXEL_RENDERING' /usr/include/freetype2/freetype/config/ftoption.h

# BCI (bytecode interpreter) — built-in on Arch/Manjaro
pacman -Q freetype2
```

### 2. Check fontconfig state

```bash
# User config
cat ~/.config/fontconfig/fonts.conf

# System config (which symlinks are active)
ls -la /etc/fonts/conf.d/ | grep -E 'antialias|hinting|lcdfilter|subpixel'

# Available configs
ls /usr/share/fontconfig/conf.avail/ | grep -E '09|10|11'
```

### 3. Check GTK settings

```bash
gsettings get org.gnome.desktop.interface font-antialiasing
gsettings get org.gnome.desktop.interface font-hinting
gsettings get org.gnome.desktop.interface font-rgba-order
```

### 4. Check Qt/KDE settings

```bash
# KDE font rendering
grep -E 'Xft|font' ~/.config/kdeglobals | grep -v '^#'

# KDE DPI override
cat ~/.config/kcminputrc 2>/dev/null | grep -A2 '\\[Fonts\\]'
```

### 5. Check Freetype env vars

```bash
grep -r 'FREETYPE' /etc/environment /etc/environment.d/ ~/.config/environment.d/ 2>/dev/null || echo "Not set"
```

### 6. Check XWayland / Xresources

```bash
cat ~/.Xresources 2>/dev/null || echo "No .Xresources"
cat ~/.Xdefaults 2>/dev/null || echo "No .Xdefaults"
```

### 7. Compute actual DPI

```bash
# For a 3440×1440 @ 34" ultrawide:
echo "scale=1; sqrt(3440^2 + 1440^2) / 34" | bc
# → ~110
```

## Recommended Configuration

### Fontconfig (`~/.config/fontconfig/fonts.conf`)

```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <!-- Subpixel RGB rendering -->
  <match target="font">
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
  </match>

  <!-- LCD light filter — less color fringing than lcddefault -->
  <match target="font">
    <edit name="lcdfilter" mode="assign"><const>lcdlight</const></edit>
  </match>

  <!-- Slight hinting — best balance for LCD at ~110 DPI+ -->
  <match target="font">
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
  </match>

  <!-- Antialiasing on -->
  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
  </match>

  <!-- Embedded bitmaps off (avoids ugly bitmap strikes for good TT fonts) -->
  <match target="font">
    <edit name="embeddedbitmap" mode="assign"><bool>false</bool></edit>
  </match>

  <!-- Autohinter off when BCI is available -->
  <match target="font">
    <edit name="autohint" mode="assign"><bool>false</bool></edit>
  </match>
</fontconfig>
```

### System subpixel symlink (sudo required)

```bash
sudo ln -sf /usr/share/fontconfig/conf.avail/10-sub-pixel-rgb.conf /etc/fonts/conf.d/
```

Without this, Flatpak/Snap apps may lack subpixel rendering because they ignore the user-level `fonts.conf`.

### GTK (gsettings)

```bash
gsettings set org.gnome.desktop.interface font-antialiasing 'rgba'
gsettings set org.gnome.desktop.interface font-hinting 'slight'
gsettings set org.gnome.desktop.interface font-rgba-order 'rgb'
```

### Qt / KDE (kwriteconfig5)

```bash
kwriteconfig5 --file kdeglobals --group General --key XftHintStyle 'hintslight'
kwriteconfig5 --file kdeglobals --group General --key XftAntialias 'true'
kwriteconfig5 --file kdeglobals --group General --key XftSubPixel 'rgb'
kwriteconfig5 --file kdeglobals --group General --key XftDpi '110'
kwriteconfig5 --file kcminputrc --group Fonts --key forceFontDPI '110'
```

### Freetype env var (`~/.config/environment.d/99-font-rendering.conf`)

```bash
# v40 = ClearType-compatible TrueType interpreter (macOS/Windows-like)
# no-stem-darkening=0 = leave default (on for < 48ppem, improves thin strokes)
FREETYPE_PROPERTIES="truetype:interpreter-version=40 cff:no-stem-darkening=0 autofitter:no-stem-darkening=0"
```

This file is read by `systemd --user` and applies to all apps launched under the user session. Won't affect apps started before a relogin.

### XWayland (`~/.Xresources`)

```
Xft.dpi: 110
Xft.antialias: 1
Xft.hinting: 1
Xft.hintstyle: hintslight
Xft.rgba: rgb
Xft.lcdfilter: lcdlight
```

Applied on next login (loaded by xsettingsd or the display manager).

## Pitfalls

- **GTK overrides fontconfig**: Even with perfect `fonts.conf`, GTK apps use `gsettings` which defaults to `grayscale` (no subpixel). You must fix both.
- **DPI mismatch**: `/proc/cmdline` kernel `dpi=` parameter only affects the console, not X/Wayland. Set DPI in `Xresources` + `kcminputrc` + `kdeglobals` for full coverage.
- **No single setting covers everything**: You must configure all five layers independently.
- **v40 vs v35 interpreter**: v40 is the ClearType-compatible mode (default since Freetype 2.7). Never set v35 — it's the legacy mode and looks worse on LCD.
- **`hintmedium` vs `hintslight`**: On ~110 DPI displays, `hintmedium` over-sharpens and introduces artifacts. `hintslight` is the sweet spot. At standard 96 DPI, `hintmedium` may be preferred — test both.
- **`lcddefault` vs `lcdlight`**: `lcddefault` can show noticeable color fringing on IPS panels. `lcdlight` reduces this while keeping subpixel sharpness.
- **Embedded bitmaps**: Some fonts (Noto, DejaVu) ship bitmap strikes. `embeddedbitmap=false` prevents them from overriding the TrueType outlines, which look much cleaner at modern resolutions.
- **Restart required**: Changes take effect per-application on restart. For system-wide effect, log out and back in.

## Verification

After applying, re-run the diagnostic checks above. Key indicators that it worked:

| Check | Expected value |
|-------|---------------|
| `gsettings get font-antialiasing` | `'rgba'` |
| `gsettings get font-hinting` | `'slight'` |
| `cat /etc/fonts/conf.d/10-sub-pixel-rgb.conf` | Exists (symlink) |
| `grep FREETYPE_PROPERTIES ~/.config/environment.d/*.conf` | v40 interpreter set |
| `grep Xft.dpi ~/.Xresources` | 110 (or your actual DPI) |

## Reference Files

- `references/hp-x34-font-tuning.md` — real-world tuning session for 3440×1440 ultrawide on Manjaro/KDE (2026-07-25)
