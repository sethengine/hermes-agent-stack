---
source_session: 20260601_164712_ab05bd
extracted_date: 2026-07-17
category: software-development
tags: [alacritty, themes, fzf, zsh, terminal-tools]
---

# Alacritty Interactive Theme Switcher (fzf)

A fully interactive zsh-based theme switcher was built at `~/.config/alacritty/theme-switcher.zsh` with companion files `theme-preview.sh` and `theme-apply.sh`.

## How it works

- Uses Alacritty's `live_config_reload = true` — saving the config instantly applies the theme.
- **fzf** provides fuzzy search over ~168 themes from the [[alacritty-theme-repo]] (cloned to `~/.config/alacritty/themes/`).
- **LIVE mode** (default): scrolling ↑↓ instantly changes the terminal's theme.
- **PAUSED mode** (Ctrl-L toggle): scroll without applying, preview only.
- Right preview pane shows color swatches, the theme file contents, and (if `chafa` is installed) the screenshot PNG.

## Key files

| File | Purpose |
|------|---------|
| `theme-switcher.zsh` | Main launcher — fzf interface with live/paused modes |
| `theme-preview.sh` | Preview generator for fzf's right pane |
| `theme-apply.sh` | Silent apply helper via fzf's `execute-silent` |

## Quick reference

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate (applies live in LIVE mode) |
| Type | Fuzzy-search theme names |
| Ctrl-L | Toggle live mode |
| Ctrl-P | Toggle preview pane |

**⚠️ Never auto-source the script from `.zshrc`** — the `print -P` calls will flood your shell with raw escape codes. Use an alias (`alias tswitch='...'`) or run manually.
