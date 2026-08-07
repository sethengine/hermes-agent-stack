---
source_session: 20260704_175147_58c619
date: 2026-07-05
category: software
tags: [emacs, doom, marginalia, vertico, consult, orderless, fzf, completion]
---

# Doom Emacs Marginalia and Fuzzy Completion

Doom Emacs provides fzf-like fuzzy completion everywhere out of the box via `consult` + `vertico` + `orderless` + `marginalia`.

## M-x with Descriptions

`marginalia` (loaded by the `vertico` module) adds docstring annotations to `M-x` command results. Press `M-A` in the minibuffer to cycle annotation levels.

For richer annotations, add to `config.el`:
```elisp
(setq marginalia-annotator-heavy t
      marginalia-align 'right)
```

## fzf-style Fuzzy Finding

Doom's completion stack replaces fzf for common operations:

| Binding | What it does |
|---------|-------------|
| `SPC .` | Fuzzy find files in project |
| `SPC s l` | Fuzzy search lines in current file |
| `SPC s g` | Ripgrep across project |
| `SPC b b` | Buffers + recent files + bookmarks |
| `SPC r r` | Find recent files |

`orderless` provides multi-word fuzzy matching (e.g. `sign int` matches `signal-integer`).

## fzf Binary

`/usr/bin/fzf` is available on the system. Can be run from `M-x shell` → `fzf`, or the Emacs `fzf` package can be added for tighter integration.

## Related
- [[doom-emacs-ui-modules]] — Module configuration
- [[doom-emacs-ide-setup]] — Core IDE setup
