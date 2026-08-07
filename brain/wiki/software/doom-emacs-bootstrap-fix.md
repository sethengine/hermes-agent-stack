---
source_session: 20260704_175147_58c619
date: 2026-07-04
category: software
tags: [emacs, doom, bootstrap, init, manjaro]
---

# Doom Emacs Bootstrap Fix (doom-nosync-error)

**Problem:** Doom Emacs crashes on startup with `doom-nosync-error` — the profile init file (`profiles.el`) is missing because `doom sync` was never run.

**Root cause:** Doom wasn't bootstrapped after installation. `early-init.el` loads `doom.el`, calls `doom-initialize`, which fails without a profile loader at `~/.local/share/doom/profiles.el`.

## Fix

1. **Create `~/.config/doom/`** (`DOOMDIR`) with `init.el`, `config.el`, `packages.el` (copy from Doom repo example files)
2. **Run `doom sync`** — this builds the profile loader, installs `straight` package manager, clones 15+ core packages, generates `init.30.2.el`
3. **Add `~/.config/emacs/bin` to `$PATH`** so `doom` command is available

After these steps, Emacs starts normally. Subsequent customization goes in `~/.config/doom/init.el` → `doom sync` → restart.

## Font rendering on Wayland

Emacs on Manjaro (`emacs 30.2-3`) has GTK3+Cairo+HarfBuzz but **no PGTK** — it runs under XWayland. For native Wayland with correct DPI:

```
yay -S emacs-pgtk
GDK_BACKEND=wayland emacs
```

See [[emacs-font-rendering-wayland]] for full font config.

## Relevant existing graph nodes

- [[manjaro_specs_manjaro]] — Manjaro Linux (OS context)
- [[kwin_latency_display]] — 3440x1440 display (DPI context)
