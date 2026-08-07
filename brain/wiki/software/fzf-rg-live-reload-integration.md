---
source_session: 20260611_000856_61266b
date: 2026-06-11
category: software
tags: [fzf, zsh, shell, ripgrep, terminal]
---

# fzf Shortcuts and rg Integration in Zsh

## Default Key Bindings

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Paste selected files/dirs into command line |
| `Alt+C`  | `cd` into selected directory |
| `Ctrl+R` | Reverse-search command history with fuzzy matching |

## Advanced: rg as fzf Source with Live Reload

```zsh
RELOAD="reload:rg --column --color=always --smart-case {q} $PWD || :" fzf --disabled --ansi \
     --bind "start:$RELOAD" --bind "change:$RELOAD"
```

### Key Patterns

- **`--disabled`** — Disables fzf's built-in filter when using an external search command like rg
- **`--bind "start:$RELOAD"` / `--bind "change:$RELOAD"`** — Runs the reload action on start and on every query change
- **`{q}`** — fzf placeholder for current query text
- **`|| :`** — Ensures rg always exits 0 (fzf's `reload:` requires exit 0)
- **`$PWD`** — Pass absolute path to rg so it outputs absolute paths in results (use double quotes for assignment-time expansion)

[[fzf-rg-live-reload]] [[alacritty-url-hints]]
