---
source_session: "20260704_175147_58c619"
category: software
date: "2026-07-04"
---

# Doom Emacs IDE/Language Setup

## Core IDE features (already enabled by default)
| Feature | Doom Module | Implementation |
|---------|-------------|----------------|
| Autocomplete popup | `corfu +orderless` + `cape` | In-buffer completion |
| LSP intellisense | `(lsp +eglot)` | Emacs 30 built-in Eglot + external LSP servers |
| Error linting | `syntax` | Flycheck red underlines |
| Syntax highlighting | `tree-sitter` | Emacs 30 built-in tree-sitter |
| Go-to-definition | `lookup` | `gd` / `K` / `SPC l d` |

## For C++ (via `(cc +lsp)`)
- Eglot auto-detects `clangd` when opening `.cpp`/`.hpp` files
- Full intellisense: completions, errors, jump-to-def, rename, hover docs
- Requires `clangd` installed on the system

## Language modules
Doom supports 60+ language modules under `:lang`. For each:
1. Uncomment the module line in `init.el`
2. Run `doom sync`
3. Restart

Common langs: `python`, `(rust +lsp)`, `json`, `yaml`, `web` (HTML/CSS/JS), `data` (TOML/INI/env), `(cc +lsp)`.

## Major pitfall
Enabling 60+ language modules simultaneously can cause `straight.el` repo corruption when `doom sync` times out or is interrupted (multiple repos get stuck in a half-cloned state).

## Related
- [[doom-emacs-bootstrap-fix]]
- [[doom-emacs-straight-package-recovery]]
