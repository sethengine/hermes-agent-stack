---
source: "20260704_201826_18967e"
date: "2026-07-04"
category: "software"
---

# Doom Emacs: Missing deflate.el on Manjaro

Manjaro's `emacs 30.2-3` package does **not** ship `deflate.el` (should be at `/usr/share/emacs/30.2/lisp/net/deflate.el`). The library was added after the 30.2 release tarball.

## Symptom

`doom doctor` crashes with:

```
Cannot open load file: No such file or directory, deflate
```

Caused by `plantuml-mode` requiring `deflate` for zlib compression.

## Fix

Install a minimal stub that provides `deflate-zlib-compress` using `gzip`:

```elisp
;; deflate.el — minimal stub for plantuml-mode
(defun deflate-zlib-compress (data)
  "Compress DATA using gzip."
  (with-temp-buffer
    (set-buffer-multibyte nil)
    (insert data)
    (call-process-region (point-min) (point-max) "gzip" t t nil "-c")
    (buffer-string)))
```

Saved to `/usr/share/emacs/30.2/lisp/net/deflate.el`.

## Related

- [[doom-emacs-custom-el-auto-load]]
