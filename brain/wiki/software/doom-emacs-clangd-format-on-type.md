---
source_session: 20260704_175147_58c619
date: 2026-07-05
category: software
tags: [emacs, doom, cpp, clangd, eglot, formatting]
---

# Doom Emacs Clangd Format-on-Type Fix

**Problem:** In Doom Emacs with `(cc +lsp)`, pressing Enter in C++ files causes the code to collapse/merge lines instead of inserting a newline. Clangd reformats the entire buffer on every keystroke.

**Root cause:** Clangd has format-on-type enabled by default. When `eglot` is used as the LSP client, clangd's formatting capability rewrites the buffer after every Enter press, which can collapse brace blocks and merge lines.

## Fix

Add these lines to `~/.config/doom/config.el` to tell eglot to ignore clangd's formatting capability:

```elisp
(add-to-list 'eglot-ignored-server-capabilities :documentFormattingProvider)
(add-to-list 'eglot-ignored-server-capabilities :documentRangeFormattingProvider)
```

After adding, restart Emacs. This preserves:
- ✅ Autocomplete (corfu)
- ✅ Intellisense (type info, hover docs)
- ✅ Diagnostics (red underlines on errors)
- ✅ Jump to definition / references
- ❌ No more clangd rewriting code on Enter

Format-on-save (`(format +onsave)`) still works — handled by `apheleia` separately on `C-x C-s`.

## Quick Test

Before config edit, temporarily disable with:
- `M-x electric-indent-mode` — toggle electric indentation
- `M-x format-all-mode` — toggle format-all

## Related
- [[doom-emacs-ide-setup]] — Core C++ LSP setup with eglot + clangd
- [[doom-emacs-eglot-cpp-autocomplete]] — Eglot auto-start and corfu auto-popup for C++
