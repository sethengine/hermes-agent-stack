---
source_session: 20260704_175147_58c619
date: 2026-07-05
category: software
tags: [emacs, doom, cpp, eglot, corfu, lsp, clangd]
---

# Doom Emacs Eglot C++ Autocomplete Fix

**Problem:** LSP autocomplete and intellisense don't work for C++ files in Doom Emacs — eglot doesn't auto-start or clangd can't find compilation flags.

## Fixes Applied

| Issue | Fix |
|-------|-----|
| **Eglot not auto-starting** | Added explicit hooks so `eglot-ensure` runs on C/C++ file open |
| **Clangd config** | Added `--background-index` and `--header-insertion=never` flags |
| **Corfu auto-popup** | Set `corfu-auto t` — completions pop up after 2 chars / 0.2s |
| **Tree-sitter grammars** | Built and installed C and C++ tree-sitter grammars for syntax highlighting |

## Test

Open a `.cpp` file in Emacs:
- `eglot` starts in minibuffer (or `M-x eglot` manually)
- Corfu popup appears as you type
- Red underlines from clangd diagnostics
- `M-x eglot-rename` to rename symbols

## If clangd is still slow or incomplete

Create a `compile_commands.json`:
```sh
cd ~/your-cpp-project
bear -- cmake -B build . && cmake --build build
```

For simple files, a `compile_flags.txt` in the project root works.

## Related
- [[doom-emacs-ide-setup]] — Core Doom IDE/LSP architecture
- [[doom-emacs-clangd-format-on-type]] — Disabling clangd format-on-type when Enter breaks code
