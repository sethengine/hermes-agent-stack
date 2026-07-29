# Session: Doom Emacs startup error + font rendering tuning + module setup

## Context
Manjaro Linux, KDE Wayland 6.5.6, Emacs 30.2-3 (GTK3 build, NOT PGTK — runs under XWayland).
3440x1440 @ 34" (~109 DPI). Intel Ultra 7 265K, RTX 5060 Ti.

## Error (session 1)

**Doom not initialized** — `doom sync` never run. Profile loader missing.

Backtrace:
```
(let (file-name-handler-alist) (let ((debug (getenv-internal "DEBUG"))) ...)
  load-with-code-conversion("early-init.el" ...)
  load("early-init" noerror nomessage)
  startup--load-user-init-file(...)
  command-line()
  normal-top-level()
```

Actual error type: `doom-nosync-error` (signaled by `doom-initialize` when profile init file absent in interactive mode).

## Fix (session 1)
1. Create `~/.config/doom/` with `init.el`, `config.el`, `packages.el` (from `static/*.example.el`)
2. Add `~/.config/emacs/bin` to `$PATH`
3. Run `doom sync` — builds profile loader + installs packages + generates profile init file

## Emacs build details
```
system-configuration-features: ACL CAIRO DBUS FREETYPE GIF GLIB GMP GNUTLS GPM
  GSETTINGS HARFBUZZ JPEG LCMS2 LIBOTF LIBSYSTEMD LIBXML2 M17N_FLT MODULES
  NATIVE_COMP NOTIFY INOTIFY PDUMPER PNG RSVG SECCOMP SOUND SQLITE3 THREADS
  TIFF TOOLKIT_SCROLL_BARS TREE_SITTER WEBP X11 XDBE XIM XINPUT2 XPM GTK3 ZLIB
```
- Cairo: yes, HarfBuzz: yes, PGTK: **no** (XWayland), GTK3: yes

### ⚠️ strings detection trap
`strings /usr/bin/emacs | grep pgtk` returns a match (the string exists in a build artifact path), but `system-configuration-features` does NOT contain `PGTK`. Always use the latter for the authoritative answer.

## Font rendering config applied

### `~/.config/fontconfig/fonts.conf`
Set `lcdfilter=lcddefault`, cleaned up duplicate hinting blocks, removed redundant `Liberation` fallbacks.

### `~/.config/doom/config.el`
- `doom-font` → JetBrainsMono Nerd Font 12pt
- `doom-symbol-font` → Symbols Nerd Font Mono
- `line-spacing 0.15`
- `x-underline-at-descent-line t`

## Doom modules enabled (session 2)

### Font/typography modules
- `ligatures` — font ligature support
- `(emoji +unicode)` — emoji rendering
- `indent-guides` — visual indentation bars
- `zen` — distraction-free writing

### Beginner-friendly modules
- `treemacs` — file tree sidebar
- `tabs` — tab bar at top
- `shell` — shell inside Emacs
- `editorconfig` — auto `.editorconfig` compliance
- `(format +onsave)` — auto-format on save
- `(spell +flyspell)` — spell check
- `smooth-scroll` — smooth scrolling
- `nav-flash` — cursor flash after motions

## Doom modules enabled (session 3)

### LSP + intellisense + highlighting
Already enabled in the stock init.el from static/init.example.el:
- `(lsp +eglot)` — Eglot (built-in Emacs 30 LSP client)
- `tree-sitter` — built-in syntax highlighting via tree-sitter
- `syntax` — flycheck linting
- `corfu +orderless` — completion popup

### All language modules (enabled via batch uncomment)
Every `:lang` module was uncommented — ~360 packages total. C++ specifically: `(cc +lsp)`.

## Broken repo batch fix
After a `doom sync` timeout (3m), N repos can be left as empty git dirs (0 commits, `git rev-parse HEAD` → `fatal: ambiguous argument 'HEAD'`). Batch detection:
```bash
STRAIGHT=~/.config/emacs/.local/straight/repos
for d in "$STRAIGHT"/*/; do (cd "$d" && git rev-parse HEAD 2>/dev/null 1>&2 || echo "$d"); done
```
Happened to: overseer.el, eglot, nose, janet-mode. Removed each with `rm -rf`, then re-ran `doom sync`. Total after fix: 360 packages, clean.

## Pitfalls hit
- **First `doom sync` timed out at 180s** — was building `overseer.el`. Re-run completed it.
- **Second `doom sync` hit overseer.el empty repo** — the previous interrupted clone left a git dir with 0 commits (`git rev-parse HEAD` → fatal). Fix: `rm -rf .local/straight/repos/overseer.el/ && doom sync`.
- **Shell cwd broken after repo delete** — because cd'd into the deleted repo. Fix: use `workdir=/home/sethengine` on the next terminal call to recover.

## Available Nerd Fonts on this system
Notable ones: JetBrainsMono Nerd Font, FiraCode Nerd Font, ZedMono Nerd Font Mono, 0xProto Nerd Font Mono, VictorMono Nerd Font Mono, CaskaydiaMono Nerd Font Mono, UbuntuMono Nerd Font, Inconsolata (various weights), AdwaitaMono Nerd Font.
