# Session: Doom Emacs settings persistence + deflate.el fix

## Context
Manjaro Linux, Emacs 30.2-3 (GTK3 build, NOT PGTK — XWayland on KDE Wayland 6.5.6).
DOOMDIR: `~/.config/doom/`. Doom install: `~/.config/emacs/`.

## Problem 1: settings lost on every restart

**Symptom**: `M-x customize`-saved settings (desktop-save-mode, save-place-mode, column-number-mode, menu-bar-mode, etc.) don't persist across Emacs restarts.

**Root cause**: Doom does **not** auto-load `custom.el`. The file existed at `~/.config/doom/custom.el` with valid `custom-set-variables` forms, but `config.el` had no code to load it. Settings were written to disk on `M-x customize-save` but never read back on startup.

**Fix** appended to `~/.config/doom/config.el`:
```elisp
(setq custom-file (expand-file-name "custom.el" doom-user-dir))
(when (file-exists-p custom-file)
  (load custom-file))
```

**Collateral cleanup**: `custom-set-faces` in `custom.el` had a `(default ((t (:family "SF Mono" ...))))` face — SF Mono is macOS-only and won't resolve on Linux. Removed the entire `custom-set-faces` form (replaced with empty `()`).

## Problem 2: `doom doctor` runtime error — `deflate` missing

**Symptom**:
```
x There was an unexpected runtime error
  Message: File is missing
  Details: ("Cannot open load file" "No such file or directory" "deflate")
  Backtrace:
    (require deflate)
    (require plantuml-mode nil t)
    ...
```

**Root cause**: `deflate.el` was added to Emacs' `lisp/net/` after the 30.2 release tag (it exists on the emacs-30 branch but was not in the 30.2 release tarball). `plantuml-mode` unconditionally does `(require 'deflate)` at line 82. No Emacs package on this system provides it.

Verified:
- `emacs --batch --eval="(require 'deflate)"` fails — library absent
- `ls /usr/share/emacs/30.2/lisp/net/deflate*` — file does not exist
- `tar -tf emacs-30.2.tar.xz | grep deflate` — not in the release tarball
- `pacman -Ql emacs | grep deflate` — not in the Manjaro package

**Fix**: Install a minimal stub that provides `deflate-zlib-compress` using external `gzip` (since Emacs 30.2 only has zlib *de*compression, not compression):
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

After fix: `doom doctor` shows normal plantuml warnings (`! Couldn't find plantuml.jar`, `! Couldn't find java`) instead of a crash.

## Residual: Symbola font
`doom doctor` warns about missing Symbola (fallback font for obscure Unicode). Non-critical — Noto Color Emoji and Apple Color Emoji are already installed. Install from AUR: `yay -S ttf-symbola`. Or use the older free version: `yay -S ttf-symbola-free`.
