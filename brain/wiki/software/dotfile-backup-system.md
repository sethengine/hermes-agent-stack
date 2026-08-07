---
source_session: 20260722_201043_61539f
updated_session: 20260725_210039_d6e241
date: 2026-07-23
updated: 2026-07-30
category: software
tags: [dotfiles, backup, restore, github, cron, automation, hermes-skill, secret-redaction]
---

# Dotfile Backup System

A complete dotfile backup and restore system at `~/.dotfiles/` connected to a private GitHub repo `github.com/sethengine/dotfiles` with daily cron automation.

## Component Files

| File | Purpose |
|------|---------|
| `~/.dotfiles/backup.sh` | Copies tracked files from `$HOME` → repo, commits, logs, pushes; has secret redaction for `.env` files, auto-removes orphan entries |
| `~/.dotfiles/restore.sh` | Restores from repo → `$HOME` (dry-run, --apply, --list modes) |
| `~/.dotfiles/dotfiles.txt` | File manifest — 76 entries tracked |
| `~/.dotfiles/README.md` | Full documentation with restore instructions |
| `~/.dotfiles/LOG.md` | Timestamped backup run log |
| `~/.dotfiles/.gitignore` | Excludes 114M Alacritty theme repos |

## Tracked Categories (76 entries)

- **Shell env**: `.zshenv`, `.xprofile`
- **Environment vars**: `.config/environment.d/` (6 files — NVIDIA, KWin tearing, build vars, OpenCode) + `.config/plasma-workspace/env/` (5 scripts — Wayland, KWin GL, cursor) + `.config/wayland-env.sh`
- **Graphics**: `.config/dxvk/dxvk.conf`
- **KDE apps**: konsolerc, dolphinrc, spectaclerc, krunnerrc, kscreenlockerrc, klipperrc, baloofilerc, kactivitymanagerdrc, kwalletrc, kded5rc, kded6rc, plasma-localerc, plasmarc, kcminputrc, kxkbrc, kgammarc, kglobalshortcutsrc, and more
- **GTK legacy**: `.gtkrc-2.0`, `.config/gtkrc`, `.config/gtkrc-2.0`
- **Audio**: `.config/pipewire/pipewire-pulse.conf`, `.asoundrc`, `.config/pipewire/client.conf`, `.config/wireplumber/main.lua.d/`
- **Git**: `.gitconfig`
- **systemd**: `.config/systemd/user/` (pueued.service, dotfiles-backup.timer, dotfiles-backup.service, etc.)
- **Emacs**: `.config/doom/` recursively
- **Cursor/themes**: `.icons/default/index.theme`

## Key Features

- **Secret redaction**: `.env` files are redacted (secrets stripped) before backup to prevent credential leaks.
- **Orphan cleanup**: `backup.sh` directory sync step auto-removes files in the backup dir that no longer exist in `$HOME`, preventing stale config accumulation (removed 3 orphan KWin cursor/latency files).
- **Mapping documentation**: A mapping doc tracks provenance for each config entry (original source path → backup path).

## GitHub Integration

- Repo: `github.com/sethengine/dotfiles` (private)
- Initial push: 33 files, 59 entries
- Daily cron via systemd timer and `cronjob` Hermes tool for redundancy

## Hermes Skill

Saved as the `dotfile-backup` skill — invocable from any session via `/dotfile-backup` or `hermes skills run dotfile-backup`.

See also: [[github-stack-sync-skill]], [[hermes-memory-systems-overview]]
