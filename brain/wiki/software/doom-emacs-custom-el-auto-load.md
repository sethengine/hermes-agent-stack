---
source: "20260704_201826_18967e"
date: "2026-07-04"
category: "software"
---

# Doom Emacs: Auto-Load custom.el

Doom Emacs does **not** auto-load `custom.el`. Settings placed there by `M-x customize` are lost on every restart unless explicitly loaded.

## Fix

Add to `~/.config/doom/config.el`:

```elisp
(setq custom-file (expand-file-name "custom.el" doom-user-dir))
(when (file-exists-p custom-file)
  (load custom-file))
```

## Context

- DOOMDIR: `~/.config/doom/`
- Emacs install: `~/.config/emacs/`
- Profile: `~/.local/share/doom/profiles.el`
- Emacs 30.2 GTK3 (XWayland on KDE Wayland) on Manjaro
- Font: JetBrainsMono Nerd Font 12pt via `doom-font`
- macOS fonts (SF Mono) in custom.el won't resolve on Linux — remove them

## Related

- [[doom-emacs-deflate-missing]]
