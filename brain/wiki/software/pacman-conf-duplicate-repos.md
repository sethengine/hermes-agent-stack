---
source: "20260726_025237_c4b845"
date: "2026-07-26"
category: "software"
tags: [pacman, yay, cachyos, repository, duplicate, pacman-conf]
wiki-links: [yay_aur_wrapper_alpm]
---

# Duplicate CachyOS Repo Entries in pacman.conf Break yay

## The Problem

`yay -Qu` fails with: `Database should be null: failed to register sync database`. This occurs when the same repository section appears **more than once** in `/etc/pacman.conf`.

On systems with CachyOS repos (`cachyos-v3`, `cachyos-core-v3`, `cachyos-extra-v3`), a common cause is duplicate entries — the same repo section appearing twice in the file. libalpm (the backend for both `pacman` and `yay`) gets confused by the duplicate declaration.

## The Fix

Open `/etc/pacman.conf` and ensure each repo section appears **exactly once**:

```bash
sudo nano /etc/pacman.conf
# or
sudo vim /etc/pacman.conf
```

Look for duplicate sections like:
```
[cachyos-v3]        ← first declaration
...
[cachyos-v3]        ← DUPLICATE — remove this
```

Remove the duplicate copy (typically the second occurrence). `pacman -Sy` will just warn about duplicates, but `yay -Qu` fails hard.

## Verification

```bash
yay -Qu    # Should now run clean and show pending updates
```

## Related

- [[yay_aur_wrapper_alpm]] — yay AUR wrapper and ALPM interaction
