---
source_session: "20260704_175147_58c619"
category: software
date: "2026-07-04"
---

# Emacs Font Rendering on Wayland/XWayland

## Context
Manjaro's `emacs 30.2-3` is a GTK3 build with Cairo and HarfBuzz but **not PGTK**. It runs under XWayland by default, which affects DPI handling and font rendering.

## Fontconfig tweaks (system-level)
Add `lcdfilter=lcddefault` to `~/.config/fontconfig/fonts.conf` — reduces color fringing on subpixel LCD text, biggest single visual improvement.

## Doom font variables (in `config.el`)
- `doom-font` — primary coding font (e.g., JetBrainsMono Nerd Font 12pt)
- `doom-variable-pitch-font` — prose/org (e.g., Noto Sans 13)
- `doom-serif-font` — fixed-pitch-serif
- `doom-symbol-font` — Symbols Nerd Font Mono
- `doom-big-font` — presentation mode size 18

## Cairo rendering fine-tune (in `config.el`)
```elisp
(setq x-underline-at-descent-line t)
(setq-default line-spacing 0.15)
(when (featurep 'cairo)
  (setq cairo-antialias 'subpixel))
```

## DPI on Wayland
Under XWayland, DPI comes from KDE's `xsettingsd`. Set in **System Settings → Fonts → Force font DPI** to 109 (for 3440x1440 @ 34"). Alternative: install `emacs-pgtk` from AUR for native Wayland support.

## Related
- [[doom-emacs-bootstrap-fix]]
