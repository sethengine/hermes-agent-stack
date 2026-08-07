---
category: system
source_session: 20260726_020103_8ad5f6
date: 2026-07-29
tags: [manjaro, arch, disk-cleanup, maintenance, pacman]
---

# Manjaro / Arch Root Disk Cleanup

Commands and strategies for freeing space on the root partition of Manjaro Linux (Arch-based).

## Quick Cleanup Sequence

```bash
# 1. Clear package cache
sudo pacman -Scc
sudo paccache -rk1          # keep only latest 1 version

# 2. Remove orphaned packages
pacman -Qtdq | sudo pacman -Rns -

# 3. Trim systemd journal
sudo journalctl --vacuum-time=2d   # or --vacuum-size=500M

# 4. Clear temp files
sudo rm -rf /tmp/* /var/tmp/*

# 5. Flatpak (if used)
flatpak uninstall --unused
```

## Key Wins

- **Orphaned packages** (`pacman -Qtdq`) can reclaim 5+ GB — old KDE5 libs, superseded compilers, unused runtimes
- **Package cache** (`/var/cache/pacman/pkg/`): several GB after `pacman -Scc`
- **journald** logs: usually modest on desktops, but worth checking with `journalctl --disk-usage`

## ⚠️ Pitfall: Orphans May Include Build Tools

Always inspect orphan list before removing — see [[manjaro-build-tools-recovery]]. Essential tools like `cmake`, `meson`, `ninja`, `rust`, `go` can appear as orphans.

## Related

- [[manjaro-build-tools-recovery]]
- `man paccache` · `man journalctl`
