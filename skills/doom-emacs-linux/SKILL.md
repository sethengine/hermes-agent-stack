---
name: doom-emacs-linux
title: Doom Emacs on Linux
description: Install, troubleshoot, configure, and optimize Doom Emacs on Linux — startup errors, font rendering, modules, and platform-specific pitfalls.
category: software-development
tags: [emacs, doom, fonts, wayland, linux, fontconfig, cairo]
triggers:
  - user mentions Doom Emacs error, Emacs startup failure
  - user asks about Emacs font rendering, fontconfig, Cairo, HarfBuzz
  - user configures a new Doom Emacs install
  - user asks about Emacs DPI or display backend (Wayland vs X11 vs PGTK)
---

# Doom Emacs on Linux

## ⚠️ Always check the display backend first

Before giving platform-specific display or font advice, check what backend Emacs is running under:

```bash
# In an already-running GUI session:
emacs --batch --eval="(message \"features: %s\" system-configuration-features)"

# Or from the binary:
strings /usr/bin/emacs-30.2 | grep -iE 'pgtk|x11 toolkit|wayland|USE_GTK|HAVE_PGTK|HAVE_X11'
ldd /usr/bin/emacs | grep -iE 'wayland|x11|gtk'
```

**Interpretation:**
- `PGTK` in `system-configuration-features` = native Wayland build (runs as `GDK_BACKEND=wayland`)
- `X11` in features but NOT `PGTK` = runs under XWayland on Wayland
- Both X11 + Wayland libs linked but no `PGTK` = GTK3 build that can use either via `GDK_BACKEND`

**⚠️ Caveat — `strings` lures you wrong**: Do NOT rely on `strings /usr/bin/emacs | grep pgtk` to detect PGTK. The binary may contain the string `pgtk` in a source path or build artifact while NOT actually having `PGTK` in `system-configuration-features` (observed on Manjaro's `emacs 30.2-3`). Always use `emacs --batch --eval="(message \"%s\" system-configuration-features)"` for the authoritative answer.

**Consequences:**
- XWayland → DPI comes from X11 layer (`xsettingsd` / KDE font settings), not native Wayland
- PGTK → native Wayland DPI, no XWayland translation
- Always tailor DPI/font advice to the actual backend, not `$XDG_SESSION_TYPE`

---

## 1. Startup error diagnosis

### Common: `doom sync` not run

Doom generates a profile init file during `doom sync`. If missing, Emacs errors with `doom-nosync-error`.

**Backtrace signature:**
```
startup--load-user-init-file → load early-init.el → doom-initialize → doom-nosync-error
```

**Check:**
```bash
ls ~/.local/share/doom/profiles.el       # profile loader
ls ~/.config/doom/                        # user config (init.el, config.el, packages.el)
```

**Fix:**
```bash
export PATH="$HOME/.config/emacs/bin:$PATH"
doom sync
```

### Settings lost on restart: custom-file not loaded

Doom does **not** auto-load `custom.el`. Settings saved via `M-x customize` (`custom-set-variables`) are silently ignored on next startup unless explicitly loaded.

**Fix** in `~/.config/doom/config.el`:
```elisp
(setq custom-file (expand-file-name "custom.el" doom-user-dir))
(when (file-exists-p custom-file)
  (load custom-file))
```

Then restart. Without this, `desktop-save-mode`, `save-place-mode`, `column-number-mode`, etc. never reapply.

### Other startup diagnostics
```bash
# Batch load with debug on:
emacs --batch --eval="(setq debug-on-error t)" -l ~/.config/emacs/early-init.el

# Check Emacs version compatibility:
emacs --version
cat ~/.config/emacs/.doom   # Doom version
```

---

## 2. Font rendering stack on Linux

### System-level: fontconfig

Fontconfig controls hinting, anti-aliasing, subpixel rendering, and LCD filter for ALL applications including Emacs.

**Key settings in `~/.config/fontconfig/fonts.conf`:**
```xml
<match target="font">
  <edit mode="assign" name="rgba"><const>rgb</const></edit>
</match>
<match target="font">
  <edit mode="assign" name="hinting"><bool>true</bool></edit>
  <edit mode="assign" name="hintstyle"><const>hintslight</const></edit>
</match>
<match target="font">
  <edit mode="assign" name="antialias"><bool>true</bool></edit>
</match>
<match target="font">
  <edit mode="assign" name="lcdfilter"><const>lcddefault</const></edit>
</match>
```

`lcdfilter=lcddefault` is the biggest single improvement — reduces color fringing.

Verify fontconfig is picking up your config:
```bash
fc-match Serif
fc-match Sans
fc-match Monospace
```

### Emacs-level: Cairo + HarfBuzz

Check what your Emacs build has:
```bash
emacs --batch --eval="(message \"features: %s\" system-configuration-features)"
```

HarfBuzz provides OpenType shaping (ligatures, complex scripts). Cairo provides anti-aliased rendering.

In `config.el`:
```elisp
(when (and (featurep 'cairo) (display-graphic-p))
  (setq x-underline-at-descent-line t)
  (setq-default line-spacing 0.15))
```

### DPI on Wayland

- **XWayland**: DPI set via KDE System Settings → Fonts → Force DPI, or via `xsettingsd`
- **PGTK**: DPI is auto-detected from the Wayland compositor
- Force Emacs DPI: `(setq frame-resolution-alist '((display . 109)))` (adjust for your monitor)

Formula: `DPI = sqrt(width² + height²) / diagonal_inches`

---

## 3. Doom font variables

Set these in `~/.config/doom/config.el`:

```elisp
;; Primary coding font (Nerd Font variant for icons)
(setq doom-font (font-spec :family "JetBrainsMono Nerd Font" :size 12))

;; Variable-pitch for org/prose
(setq doom-variable-pitch-font (font-spec :family "Noto Sans" :size 13))

;; Symbol/emoji fallback
(setq doom-symbol-font (font-spec :family "Symbols Nerd Font Mono"))

;; Big font for presentations
(setq doom-big-font (font-spec :family "JetBrainsMono Nerd Font" :size 18))
```

Font names must match exactly what `fc-list` returns. Run `M-x describe-font` in Emacs to verify.

After changing, reload: `M-x doom/reload-font`

---

## 4. Modules for font/typography

In `~/.config/doom/init.el`, under `:ui`:

| Module | Flag | Purpose |
|--------|------|---------|
| `ligatures` | — | Font ligature support |
| `emoji` | `+unicode` | Emoji rendering via font fallback |
| `indent-guides` | — | Visual indentation guides |
| `zen` | — | Distraction-free writing with variable-pitch |
| `format` | `+onsave` | Auto-format code on save (under `:editor` section) |
| `spell` | `+flyspell` | Underlines misspelled words as you type (under `:checkers`) |

After editing `init.el` → `doom sync` → restart Emacs.

## 5. Beginner-friendly modules (low-friction additions)

These help new users feel at home in Doom without a learning cliff. Enable as a batch in `~/.config/doom/init.el`:

| Module | Section | What it does |
|--------|---------|-------------|
| `treemacs` | `:ui` | File tree sidebar — `SPC t t` toggles, familiar VSCode/Atom paradigm |
| `tabs` | `:ui` | Tab bar at top — `SPC b TAB` or click |
| `shell` | `:term` | `M-x shell` for a bash prompt inside Emacs |
| `editorconfig` | `:tools` | Automatically respects `.editorconfig` from any project — zero config |
| `smooth-scroll` | `:ui` | Smooth scrolling instead of jumpy reposition |
| `nav-flash` | `:ui` | Brief cursor-line flash after big motions or searches — helps spatial orientation |

These bring ~9 packages total (treemacs alone pulls in ace-window, hydra, posframe, etc.). `doom sync` installs them all.

### M-x descriptions via marginalia

The `vertico` module already includes `marginalia` but expects `doom-first-input` to trigger. Ensure it's active for first `M-x` by adding to `config.el`:

```elisp
(after! marginalia
  (marginalia-mode +1))
(setq marginalia-annotator-heavy t
      marginalia-align 'right)
```

Press `M-A` in the minibuffer to cycle annotation views (brief ↔ rich ↔ heavy).

### fzf alternative: consult + vertico

No separate fzf package needed. The `consult` module (bundled with vertico) provides fzf-like fuzzy finding with better Emacs integration:

| Binding | Replaces fzf for... |
|---------|---------------------|
| `SPC .` | `fzf` file finding in project |
| `SPC s p` | `fzf` + ripgrep content search |
| `SPC s b` | fzf-like line search in buffer |
| `SPC b b` | Buffers + recent files unified |
| `SPC s g` | Project-wide ripgrep from minibuffer |

Use `orderless` completion style (already default) — multi-word fuzzy matching works like `fzf -x`.

If the user specifically wants the `fzf` binary integration, install `fzf` package via `use-package!` or use system `/usr/bin/fzf` from `M-x shell`.

### Why Evil: modal editing ergonomics

New Doom users often ask why it uses Vim keybindings. The answer is **ergonomics**, not ideology.

**Default Emacs relies on chording** — holding Ctrl/Meta while pressing other keys:
`C-c`, `C-x`, `C-v`, `C-s`, `C-a`, `C-e`, `C-p`, `C-n`, `C-f`, `C-b`, `C-k`, `C-y`...

This causes **RSI (repetitive strain injury)**, especially in the pinky from constant Ctrl. The pattern is so well-known it has a name: "Emacs pinky."

**Evil (Vim emulation) uses modal editing instead:**

| Action | Emacs chording | Vim/Evil |
|--------|---------------|----------|
| Move up/down | `C-p` / `C-n` | `j` / `k` (single keys) |
| Delete line | `C-a C-k` (chords) | `dd` (two taps) |
| Search | `C-s find C-s C-s` | `/find<CR>nn` |
| Save | `C-x C-s` (double chord) | `:w<CR>` |
| Paste | `C-y` | `p` |

Most common operations become **1-2 keystrokes with no modifiers**. The pinky stays at rest.

**Architecture reminder:** Evil is just the keypress layer. Everything good about Emacs still runs underneath — magit, org-mode, LSP, tree-sitter, elisp config. Evil is optional: comment out `(evil +everywhere)` from `init.el`, run `doom sync`, and it's standard Emacs.

---

## 6. LSP + Eglot intellisense

### Module

```elisp
;; In ~/.config/doom/init.el, under :tools:
(lsp +eglot)   ; use built-in Emacs LSP client
```

Eglot is built into Emacs 30+. The `+eglot` flag tells Doom to use Eglot instead of lsp-mode.

### How it works

Open a file and Eglot auto-detects the right LSP server from `$PATH`:

| Language | LSP server | Arch package |
|----------|-----------|-------------|
| C/C++ | `clangd` | `clang` |
| Python | `pyright` or `python-lsp-server` | `pyright` |
| Rust | `rust-analyzer` | `rust-analyzer` |
| Go | `gopls` | `go` (includes gopls) |
| JS/TS | `typescript-language-server` | `typescript-language-server` |

Eglot activates lazily on first file open in a project with a recognized config file.

### C/C++ setup (clangd)

For C++ with `(cc +lsp)` + `(lsp +eglot)`, add explicit eglot hooks to `config.el`:

```elisp
;; Force eglot startup for C/C++ modes
(add-hook 'c++-mode-hook #'eglot-ensure)
(add-hook 'c-mode-hook #'eglot-ensure)
(add-hook 'c++-ts-mode-hook #'eglot-ensure)
(add-hook 'c-ts-mode-hook #'eglot-ensure)

;; Clangd tuning
(after! eglot
  (setq eglot-autoshutdown t
        eglot-sync-connect 1
        eglot-connect-timeout 30)
  (add-to-list 'eglot-server-programs
               '((c++-mode c++-ts-mode c-mode c-ts-mode)
                 . ("clangd"
                    "--header-insertion=never"
                    "--background-index"))))
```

**Without `compile_commands.json`, clangd has no compiler flags.** Create one:

```bash
# CMake project:
cd ~/project && bear -- cmake -B build . && cmake --build build

# Simple single-file project — use compile_flags.txt instead:
echo "-std=c++23" > compile_flags.txt
echo "-I/usr/include" >> compile_flags.txt
```

### Corfu auto-completion for LSP

Ensure corfu auto-pops with LSP completions (in `config.el`):

```elisp
(setq corfu-auto t
      corfu-auto-delay 0.2
      corfu-auto-prefix 2
      corfu-popupinfo-delay '(0.5 . 0.2))
```

### What you get

| Feature | Key / Mechanism |
|---------|----------------|
| **Completions** | `corfu` popup auto-shows LSP completions |
| **Errors** | `flycheck` (from `:checkers syntax`) underlines LSP-reported errors |
| **Jump to def** | `gd` or `SPC c d` |
| **Hover docs** | `K` or `SPC c k` |
| **Rename** | `SPC c r` |
| **Code actions** | `SPC c a` |
| **Better highlighting** | `tree-sitter` module (built-in Emacs 30+) |

### Tree-sitter grammar installation

The `tree-sitter` module (`:tools` → `tree-sitter`) enables better syntax highlighting via Emacs 30's built-in tree-sitter. Doom's `cc` module registers grammar recipes in `treesit-language-source-alist`, but Emacs needs the actual grammar `.so` compiled.

**Auto-install (fails on Emacs 30.2 for some grammars):**
```emacs-lisp
M-x treesit-install-language-grammar RET cpp RET
```

On Emacs 30.2, this may fail with `treesit-error: "Cannot find recipe for this language"` because the recipe system requires entries in `treesit-language-source-alist` which Doom sets but may not be available early enough.

**Manual build (always works):**
```bash
# C grammar
git clone --depth 1 --branch v0.24.1 https://github.com/tree-sitter/tree-sitter-c.git
cd tree-sitter-c
cc -shared -fPIC -o ~/.config/emacs/tree-sitter/libtree-sitter-c.so src/parser.c -I src

# C++ grammar (includes scanner.c)
git clone --depth 1 --branch v0.23.4 https://github.com/tree-sitter/tree-sitter-cpp.git
cd tree-sitter-cpp
cc -shared -fPIC -o ~/.config/emacs/tree-sitter/libtree-sitter-cpp.so src/parser.c src/scanner.c -I src
```

**Point Emacs to the grammars** (in `config.el`):
```elisp
(after! treesit
  (add-to-list 'treesit-extra-load-path
               (expand-file-name "tree-sitter" doom-user-dir)))
```

Verify from the terminal:
```bash
emacs --batch --eval="(require 'treesit)" \
  --eval="(add-to-list 'treesit-extra-load-path \"~/.config/emacs/tree-sitter\")" \
  --eval="(message \"cpp: %s\" (treesit-language-available-p 'cpp))"
# Should print: cpp: t
```

### Install LSP servers

```bash
# For C++ (clangd):
sudo pacman -S clang

# List available servers:
pacman -Ss language-server
```

---

## 7. Enabling all language modules at once

For a beginner who wants everything working for any file:

```elisp
:lang
ada
(agda +local)
beancount
(cc +lsp)        ; C/C++ — primary
clojure common-lisp coq crystal csharp
data (dart +flutter) dhall
elixir elm emacs-lisp erlang ess
factor faust fortran fsharp fstar
gdscript (go +lsp) (graphql +lsp)
(haskell +lsp) hy idris json janet (java +lsp)
javascript julia kotlin latex lean ledger lua
markdown nim nix ocaml odin org
php plantuml graphviz purescript python
qt racket raku rest rst (ruby +rails) (rust +lsp)
scad scala (scheme +guile) sh sml solidity swift terra
web yaml zig
```

**Scale**: This installs ~360 packages. First sync may take several minutes and hit timeouts. See Pitfalls below for handling interrupted syncs.

---

## 8. Keybinding cheatsheet

After configuration is done, deliver a cheatsheet as `~/.config/doom/cheatsheet.org` — an Org-mode file the user can open in Emacs with `SPC f f` and fold sections with TAB.

**What to cover:**
- Evil (vim) motion, editing, text objects
- `SPC` leader menu — each prefix group (file, buffer, search, toggle, window, project, code, git, help, quit)
- Module-specific bindings (treemacs: `SPC t t`, tabs: `SPC t T`, shell: `SPC o t`, zen: `SPC t z`)
- Minibuffer navigation (vertico/corfu: C-j/k, M-A, M-RET, C-SPC for embark preview)
- LSP bindings (gd, K, SPC c r / a / d / D)
- Magit git operations

**Format**: Org tables. Use `#+TITLE`, `#+DATE`, `#+STARTUP: content` headers. Group by prefix key. Add a "Useful Commands by Category" table at the bottom for the most common actions.

Place at: `~/.config/doom/cheatsheet.org`

---

## 9. Pitfalls

- **Doom sync required after init.el changes**: Running `doom sync` regenerates the profile init file. Skipping it leads to stale module load state.
- **Font not found**: Emacs errors with `doom-font-error`. Check exact font name with `fc-list | grep -i "nerd font mono"` and `M-x describe-font`.
- **Nerd Font icons as boxes**: Set `doom-symbol-font` to a Nerd Font Mono variant. Run `M-x nerd-icons-install-fonts` as fallback.
- **Batch mode hides GUI errors**: `emacs --batch -l early-init.el` may succeed while GUI startup fails — the display-dependent code paths only run interactively.
- **User config vs Doom installation**: Doom source is at `~/.config/emacs/` (the framework). User config is at `~/.config/doom/` (the `$DOOMDIR`). They are separate.
- **Broken straight repos at scale**: When enabling 60+ language modules at once, `doom sync` often times out and leaves repos with empty git directories. These block future syncs. Fix — find ALL broken repos first (don't chase them one by one):

  **Method A — git rev-parse (precise):**
  ```bash
  STRAIGHT=~/.config/emacs/.local/straight/repos
  for d in "$STRAIGHT"/*/; do
    (cd "$d" && git rev-parse HEAD 2>/dev/null 1>&2 || echo "$d")
  done
  ```

  **Method B — du -sh (faster, catches empty/half-cloned dirs):**
  ```bash
  du -sh ~/.config/emacs/.local/straight/repos/*/ \
    | awk '$1 ~ /^[48]\.0K$/' \
    | cut -f2-
  ```
  Inspect the list, then `xargs rm -rf` the broken ones and re-run `doom sync`.

- **Shell cwd broken after rm -rf straight repo**: If you `cd` into a straight repo and then `rm -rf` it, the shell's cwd becomes a nonexistent path. All subsequent terminal calls fail with `getcwd: cannot access parent directories`. Fix: pass `workdir=/home/user` on the next terminal call to reset.

- **LSP server not found**: Eglot autodetects LSP servers from `$PATH`. If a server like `clangd` isn't installed, Eglot won't start and there'll be no intellisense errors, just silence. Install the required server for the language (see section 6).

- **Clangd format-on-type rewrites buffer on Enter**: Clangd has format-on-type enabled by default. In C++ files, pressing Enter triggers clangd to reformat the entire buffer — which can collapse brace blocks, merge lines, and generally make it look like "Enter is broken." The fix is to tell eglot to ignore clangd's formatting capability in `config.el`:

  ```elisp
  (add-to-list 'eglot-ignored-server-capabilities :documentFormattingProvider)
  (add-to-list 'eglot-ignored-server-capabilities :documentRangeFormattingProvider)
  ```

  This preserves autocomplete, diagnostics, jump-to-def, and hover docs. Only auto-formatting on Enter is removed. Format-on-save (`(format +onsave)` via `apheleia`) still works on `C-x C-s`.

  **Quick test without config edit**: Temporarily disable with `M-x electric-indent-mode` or `M-x format-all-mode`.

- **`deflate.el` missing on Emacs 30.2**: Emacs 30.2's release tarball omitted `deflate.el` (added to the emacs-30 branch post-release). The `plantuml-mode` package does `(require 'deflate)` and crashes with `Cannot open load file: No such file or directory, deflate`. Fix: install a minimal stub that provides `deflate-zlib-compress` using external `gzip`:

  ```bash
  sudo tee /usr/share/emacs/30.2/lisp/net/deflate.el > /dev/null << 'EOF'
  ;;; deflate.el --- Interface to zlib (RFC 1951) compression -*- lexical-binding:t -*-
  (defun deflate-zlib-compress (object &optional level)
    (with-temp-buffer
      (set-buffer-multibyte nil)
      (insert object)
      (let ((coding-system-for-write 'no-conversion)
            (coding-system-for-read 'no-conversion)
            (level (or level 6)))
        (unless (zerop (call-process-region (point-min) (point-max)
                        "gzip" t t nil "-c" (format "-%d" level)))
          (error "gzip compression failed"))))
      (buffer-string))
  (provide 'deflate)
  EOF
  ```

- **Symbola font**: Doom doctor warns if missing. It is a fallback font for obscure Unicode symbols. Non-critical — Noto Color Emoji already covers common cases. Install from AUR: `yay -S ttf-symbola`.
