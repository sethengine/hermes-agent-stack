---
name: dotfile-backup
description: Backup and restore personal dotfiles (shell, KDE, terminal, editor, audio, GTK configs) to a private GitHub repo. Includes automated daily cron, manual backup/restore scripts, and change logging.
argument-hint: 'dotfile-backup | dotfile-backup restore | dotfile-backup log'
user-invocable: true
---

# Dotfile Backup

Backup your personal dotfiles to `github.com/sethengine/dotfiles` — shell configs, KDE Plasma settings, Alacritty terminal, Doom Emacs, PipeWire/WirePlumber audio, GTK themes, htop, and rofi.

**Local repo:** `~/.dotfiles/`  
**GitHub:** `https://github.com/sethengine/dotfiles`  
**Cron:** Daily at 6:00 AM (Hermes cron job `dotfile-backup`)

## Quick Commands

| Action | Command |
|--------|---------|
| Run backup now | `bash ~/.dotfiles/backup.sh` |
| Preview restore | `bash ~/.dotfiles/restore.sh` |
| Restore files | `bash ~/.dotfiles/restore.sh --apply` |
| List repo contents | `bash ~/.dotfiles/restore.sh --list` |
| View backup log | `cat ~/.dotfiles/LOG.md` |
| View env file map | `cat ~/.dotfiles/ENV-MAP.md` |

## What's Backed Up

**Shell:** `.bashrc`, `.zshrc`, `.profile`, `.zshenv`, `.xprofile`  
**Git:** `.gitconfig`  
**Zsh Prompt:** `.p10k.zsh` (Powerlevel10k theme config)  
**Environment:** `.config/environment.d/` (build, kwin, nvidia, opencode), `.config/plasma-workspace/env/` (Wayland, KWin GL, cursor, Qt media)  
**Standalone Env Scripts:** `.config/wayland-env.sh` (Wayland/NVIDIA env vars)  
**KDE Plasma:** `kdeglobals`, `kwinrc`, `plasmashellrc`, `plasma-localerc`, `konsolerc`, `dolphinrc`, `spectaclerc`, `krunnerrc`, `kscreenlockerrc`, `klipperrc`, `baloofilerc`, `kactivitymanagerdrc`, `kwalletrc`, `kded5rc`, `kded6rc`, `kcminputrc`, `kxkbrc`, `kgammarc`, `kglobalshortcutsrc`  
**Terminal:** `.config/alacritty/alacritty.toml` + theme scripts (not 114M repos)  
**Editor:** `.config/doom/` (Doom Emacs), `.config/emacs/bin/doom-env` (Emacs env generator)  
**GTK:** `.config/gtk-3.0/`, `.config/gtk-4.0/`, `.gtkrc`, `.gtkrc-2.0`  
**Audio:** `.config/pipewire/`, `.config/wireplumber/`  
**Desktop:** `user-dirs.dirs`, `mimeapps.list`, `fontconfig`, `autostart/`  
**System services:** `systemd/user/*.service`, `systemd/user/*.timer`, `systemd/user/*.service.d/` (service drop-in overrides with env/limit configs)  
**Tools:** `.config/htop/`, `.config/rofi/`  
**Graphics:** `.config/dxvk/dxvk.conf` (DXVK config, ref'd by env var)  
**Flatpak Browser Overrides:** `.local/share/flatpak/overrides/*` (DBus integration policy for Chrome, Chromium, Firefox, LibreWolf, Waterfox)  
**Self-Hosted Services:** `firecrawl/.env` (Firecrawl self-hosted performance config)  

> **Full mapping:** See `ENV-MAP.md` for every env file's source path, app origin, and purpose.

## Restoring on a New Machine

```bash
# Clone
git clone https://github.com/sethengine/dotfiles.git ~/.dotfiles

# Restore all files to $HOME (originals backed up as .bak)
bash ~/.dotfiles/restore.sh --apply

# Re-source shell
exec zsh
```

## Backup Script

`backup.sh`:
1. Copies all tracked files from `$HOME` into `~/.dotfiles/`
2. Excludes `.git` dirs and ignores theme repos (114M of alacritty themes)
3. **Redacts secrets** from `.env` files (API keys, tokens, passwords) before commit
4. Commits with a timestamped message listing changed files
5. Appends a log entry to `LOG.md`
6. Pushes to GitHub if remote is configured

## Restore Script

`restore.sh` has three modes:
- **Default (dry-run)** — shows what would be restored, no changes made
- `--apply` — copies files from repo back to `$HOME`, backs up existing files as `.bak.<timestamp>`
- `--list` — shows all files in the repo and git log

## Cron Jobs

- **`dotfile-backup`**: Daily at 6:00 AM — runs `~/.dotfiles/backup.sh` via no_agent cron
- **`github-stack-sync`**: Daily at 5:00 AM — backs up Hermes configs/skills/sessions to `github.com/sethengine/hermes-agent-stack`

## Files

```
~/.dotfiles/
├── backup.sh            # Backup (HOME → repo)
├── restore.sh           # Restore (repo → HOME)
├── dotfiles.txt         # File manifest (83 entries)
├── ENV-MAP.md           # Env file source mapping doc
├── README.md            # This doc
├── LOG.md               # Backup run log
├── .gitignore           # Excludes theme repos, OS junk
├── .zshenv              # Shell env
├── .xprofile            # X11 profile
├── .p10k.zsh            # Powerlevel10k prompt config
├── .gtkrc-2.0           # GTK2 theme
├── firecrawl/.env       # Self-hosted Firecrawl config
├── .local/share/flatpak/overrides/  # Browser DBus policies
├── .config/
│   ├── alacritty/
│   ├── doom/
│   ├── wayland-env.sh   # Wayland/NVIDIA env script
│   ├── dxvk/dxvk.conf   # DXVK perf config
│   ├── emacs/bin/doom-env  # Emacs env generator
│   ├── environment.d/   # systemd env vars
│   ├── gtk-3.0/ & gtk-4.0/
│   ├── pipewire/ & wireplumber/
│   ├── systemd/user/    # Services, timers & drop-in overrides
│   ├── autostart/
│   ├── plasma-workspace/env/
│   └── ...              # All KDE config *.rc files
```
