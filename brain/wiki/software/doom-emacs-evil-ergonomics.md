---
source_session: 20260704_175147_58c619
date: 2026-07-05
category: software
tags: [emacs, doom, evil, vim, ergonomics, rsi, keybindings]
---

# Doom Emacs Evil Modal Editing Ergonomics

Doom Emacs uses `(evil +everywhere)` to replace default Emacs chording with Vim-style modal editing.

## The Problem with Default Emacs Keys

Default Emacs relies heavily on **chording** — holding Ctrl/Meta while pressing other keys:
`C-c`, `C-x`, `C-v`, `C-s`, `C-a`, `C-e`, `C-p`, `C-n`, `C-f`, `C-b`, etc.

This is infamous for causing **RSI (repetitive strain injury)**, especially in the pinky from constant Ctrl key usage.

## Evil (Vim) Approach

| Aspect | Emacs | Vim/Evil |
|--------|-------|----------|
| Movement | `C-p`/`C-n`/`C-f`/`C-b` (chords) | `j`/`k`/`l`/`h` (single keys) |
| Editing | `C-k`/`C-y`/`C-w` (chords) | `x`/`dd`/`yy`/`p` (single/mnemonic) |
| Search | `C-s find C-s C-s` (chord chain) | `/find<CR>nn` (modal) |
| Save | `C-x C-s` (double chord) | `:w<CR>` (2 keystrokes) |

## Architecture

Doom Emacs is **Emacs first**, not an adaptation of Vim:
1. **Emacs** is the engine (Elisp, buffers, LSP, tree-sitter, magit)
2. **Doom** is a configuration framework (curated modules, defaults)
3. **Evil** (Emacs VI Layer) adds Vim keybindings on top

Evil is optional — commenting out `(evil +everywhere)` from `init.el` and running `doom sync` returns standard Emacs keys.

## Related
- [[doom-emacs-bootstrap-fix]] — Doom bootstrap and init
- [[doom-emacs-ui-modules]] — Module configuration
