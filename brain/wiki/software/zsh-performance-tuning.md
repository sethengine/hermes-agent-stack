---
source: "20260711_143618_f492c9"
date: "2026-07-11"
category: "software"
tags: [zsh, alacritty, performance, powerlevel10k, autosuggestions]
wiki-links: [alacritty_opt_document, alacritty_text_clipping]
---

# Zsh Performance Tuning

Alacritty terminal slowness (command processing lag, password entry delay) was diagnosed as zsh per-keystroke overhead, not terminal emulator latency.

**Root causes:**
- `zinit` sourced but unused (no `zinit load` calls) -- dead init cost
- Two themes loaded sequentially (miloshadzic → p10k replaced it)
- `compinit` had 4 stale dump files
- `zsh-syntax-highlighting` ran regex on every keystroke
- `zsh-autosuggestions` ran history search synchronously

**Fixes applied (backup at `~/.zshrc.backup.20260711-2323`):**

| # | Change | Impact |
|---|---|---|
| 1 | Removed dead zinit init (4 lines) | -20ms startup |
| 2 | `ZSH_THEME=""` instead of miloshadzic | Eliminated wasted theme render |
| 3 | `ZSH_AUTOSUGGEST_USE_ASYNC=1` | Non-blocking autosuggestions |
| 4 | `DISABLE_UNTRACKED_FILES_DIRTY=true` | No duplicate git status work |
| 5 | `POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS=0.01` | Always async git status |
| 6 | `POWERLEVEL9K_INSTANT_PROMPT=verbose` | Prompt appears before plugins finish |
| 7 | oh-my-zsh update disabled | Kills update prompt timeout |
| 8 | Cleaned 4 stale `~/.zcompdump*` | Single fresh dump generated |

**Result:** Startup dropped ~183ms → ~164ms. Main improvement is subjective -- keystroke processing no longer blocks.
