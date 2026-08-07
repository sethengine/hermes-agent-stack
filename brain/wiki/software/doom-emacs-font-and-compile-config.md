---
source: "session_20260704_175147_58c619"
date: "2026-07-05"
category: "software"
tags: [emacs, doom-emacs, font, compile, config.el]
related: [[doom-emacs-ide-setup.md]]
---

# Doom Emacs Font & Compile Configuration

Set font permanently in `~/.config/doom/config.el`:
```elisp
(setq doom-font (font-spec :family "JetBrainsMono Nerd Font" :size 14))
```
Apply without restart: `M-x doom/reload-font RET`.

## Compilation for C++ (No Evil)
Set default compile command in `config.el`:
```elisp
(setq compile-command "g++ -std=c++23 -Wall -o program *.cpp && ./program")
```
**Key limitation:** The `*compilation*` buffer is output-only — programs using `std::cin` will hang. Use `SPC o t` (or `M-x shell`) for interactive programs, or `quickrun` which prompts for input separately.

## Quickrun
`M-x quickrun` runs the current buffer — great for single-file C++ tests without a compilation step.
