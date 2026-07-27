---
name: doom-emacs-setup
description: Doom Emacs configuration, troubleshooting, and keybinding reference for this user's setup. Load this skill for any future Emacs/Doom-related questions.
---

# Doom Emacs Setup

## Environment
- **Emacs**: GNU Emacs 30.2 (Manjaro pkg `emacs 30.2-3`)
- **Build**: GTK3, Cairo, HarfBuzz, tree-sitter, native-comp — **no PGTK** (runs under XWayland)
- **Display**: 3440x1440 @ ~109 DPI, KDE Wayland
- **Doom**: 3.0.0 (installed at `~/.config/emacs/`)
- **User config**: `~/.config/doom/` (DOOMDIR)
- **Package manager**: straight.el
- **Font**: JetBrainsMono Nerd Font 14pt + Symbols Nerd Font Mono (set via `doom-font` in config.el)
- **Evil**: DISABLED — user runs classic Emacs keybindings only, no modal editing

## Active Modules (init.el)
- `corfu +orderless` — autocomplete popup
- `vertico` + `consult` — fuzzy finding (file/project search)
- `(emoji +unicode)` — emoji support
- `indent-guides` — indent bars
- `ligatures` — font ligatures
- `treemacs` — file tree sidebar (SPC t t / F9)
- `tabs` — tab bar (centaur-tabs, SPC t T)
- `smooth-scroll` — smooth scrolling
- `nav-flash` — flash cursor line on navigation
- `zen` — distraction-free writing (SPC t z)
- `(lsp +eglot)` — LSP via built-in eglot
- `tree-sitter` — syntax highlighting
- `editorconfig` — auto `.editorconfig` support
- `(format +onsave)` — auto-format via apheleia
- `(spell +flyspell)` — spell checking
- `shell` — shell REPL popup (SPC o t)
- `magit` — Git client (SPC g g)
- `lookup` — go to definition/docs (gd / K)
- All language modules enabled (60+)

## Config (config.el)
- Font: JetBrainsMono Nerd Font 14pt (change `:size` number; `M-x doom/reload-font` to apply without restart)
- Symbol font: Symbols Nerd Font Mono
- Cairo render: `x-underline-at-descent-line`, `line-spacing 0.15`
- Marginalia: rich M-x annotations (M-A to cycle)
- Eglot auto-starts on C/C++ hooks
- Corfu: auto-popup after 2 chars, 0.2s delay
- Clangd flags: `--header-insertion=never`, `--background-index`
- Tree-sitter grammar path: `~/.config/emacs/tree-sitter/`
- Theme: doom-one
- Display line numbers: t

## User Disabled Evil (no Vim keybindings)

This user runs Doom with **`(evil +everywhere)` disabled** — pure Emacs keybindings (`C-x`, `C-c` prefix, no `SPC` leader). When helping them:
- Always give **plain Emacs keybindings**, not `SPC`-prefixed ones
- They use `C-x o` for window navigation, `C-x b` for buffer switching, `C-x C-f` for files
- The `SPC` key is just a space to them
- Doom still works fine without Evil — all modules function, just no modal editing

## Keybindings (Classic Emacs — Evil disabled)

### File operations
| Key | Action |
|-----|--------|
| `C-x C-f` | Find file (vertico fuzzy) |
| `C-x f` | Find file (alias) |
| `C-x C-s` | Save file |
| `C-x C-w` | Save as |
| `C-x k` | Kill (close) buffer |

### Buffer / Window management
| Key | Action |
|-----|--------|
| `C-x b` | Switch buffer (fuzzy) |
| `C-x C-b` | List all buffers (ibuffer) |
| `C-x o` | Next window |
| `C-x 0` | Close current window |
| `C-x 1` | Keep only this window |
| `C-x 2` | Split horizontal |
| `C-x 3` | Split vertical |

### Search
| Key | Action |
|-----|--------|
| `C-s` | Isearch forward |
| `C-r` | Isearch backward |
| `M-x consult-line` | Fuzzy search current buffer |
| `M-x consult-ripgrep` | Search project |
| `M-x imenu` | Jump to function/symbol |

### Help
| Key | Action |
|-----|--------|
| `C-h f` | Describe function |
| `C-h v` | Describe variable |
| `C-h k` | Describe key |
| `C-h o` | Look up symbol |
| `M-x describe-mode` | Current mode documentation |
| `M-x doom/reload-font` | Apply font changes |
| `M-x doom/reload` | Reload config |

### Completion / LSP
| Key | Action |
|-----|--------|
| `C-;` | Trigger corfu completion |
| `C-n` / `C-p` | Next/previous completion |
| `C-g` | Close completion popup |
| `M-x eglot` | Manually start LSP |
| `M-x eglot-rename` | Rename symbol |
| `M-x eglot-code-actions` | LSP code actions |

### Misc
| Key | Action |
|-----|--------|
| `M-x` | Execute command (fuzzy) |
| `M-A` | Cycle completion annotations |
| `M-x compile` | Run compile command |
| `M-x shell` | Open shell buffer |
| `M-x quickrun` | Run current file |
| `M-x toggle-debug-on-error` | Get backtraces on errors |

## C++ Development Setup
- Eglot hooks: `c++-mode-hook`, `c-mode-hook`, `c++-ts-mode-hook`, `c-ts-mode-hook` → `eglot-ensure`
- **clangd format-on-type DISABLED** — `eglot-ignored-server-capabilities` includes `:documentFormattingProvider` and `:documentRangeFormattingProvider` to prevent clangd from rewriting buffer on every Enter. If Enter still merges lines, this is the fix.
- clangd installed at `/usr/bin/clangd` (from `clang` package)
- Tree-sitter C/C++ grammars built and stored in `~/.config/emacs/tree-sitter/`
- For projects without `compile_commands.json`: create `compile_flags.txt` in project root, or use `bear -- cmake -B build .` to generate one

### Compiling C++ programs with stdin input
`M-x compile` runs the program in a read-only `*compilation*` buffer — it cannot send keyboard input to `std::cin`. **Workarounds:**
- `M-x shell` (or `M-x ansi-term`) — compile and run from a real shell: `g++ -std=c++23 -o test main.cpp && ./test`
- `M-x quickrun` — runs the file; for programs needing input, it prompts in the minibuffer
- `M-!` + pipe input from file: `./test < input.txt`

### Tree-sitter grammars (manual build)
If `treesit-language-available-p` returns nil for c/cpp:
```
mkdir -p ~/.config/emacs/tree-sitter/
git clone --depth 1 --branch v0.24.1 https://github.com/tree-sitter/tree-sitter-c.git /tmp/ts-c
cd /tmp/ts-c && cc -shared -fPIC -o ~/.config/emacs/tree-sitter/libtree-sitter-c.so src/parser.c -I src
git clone --depth 1 --branch v0.23.4 https://github.com/tree-sitter/tree-sitter-cpp.git /tmp/ts-cpp
cd /tmp/ts-cpp && cc -shared -fPIC -o ~/.config/emacs/tree-sitter/libtree-sitter-cpp.so src/parser.c src/scanner.c -I src
```
Then in config.el: `(add-to-list 'treesit-extra-load-path "~/.config/emacs/tree-sitter")`

## Known Issues & Fixes
1. **"doom sync" fails on package repos**: Sometimes `git clone` leaves an empty repo directory. Fix: `rm -rf /home/sethengine/.config/emacs/.local/straight/repos/<package>` and re-run `doom sync`
2. **Emacs started via XWayland**: Font DPI may be wrong. Uncomment `frame-resolution-alist` in config.el
3. **`doom` not in PATH**: Already added to `.zshrc` as `export PATH="$HOME/.config/emacs/bin:$PATH"`
4. **Broken git repos (overseer/eglot/nose/janet-mode)**: Empty dirs from clone timeout. Remove and re-run sync
5. **C++ Enter merges lines / deletes newlines**: Caused by clangd format-on-type. Fix in config.el: `(add-to-list 'eglot-ignored-server-capabilities :documentFormattingProvider)` (and `:documentRangeFormattingProvider`)
6. **C++ program needs stdin but `M-x compile` shows "undefined character"**: The `*compilation*` buffer is output-only. Use `M-x shell` then run the program there, or `M-x quickrun`
7. **Tree-sitter C/C++ grammar not found (`treesit-language-available-p` returns nil)**: Must build manually — grammars need `scanner.c` compiled alongside `parser.c` for C++. See C++ Development Setup section for exact build commands.

## Troubleshooting Tips
- Restart Emacs after config changes
- `doom sync` after changing `init.el`
- `M-x doom/reload-font` after changing font settings
- `M-x eglot` to manually start LSP if auto-start fails
- Check `*eglot-events*` buffer for LSP connection issues
- `M-x toggle-debug-on-error` to get backtraces
