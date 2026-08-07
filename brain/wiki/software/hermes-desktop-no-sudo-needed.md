---
source_session: "20260604_185710_e4868a"
date: 2026-06-13
category: software
tags: [hermes, desktop, sudo, permissions, appimage, installation]
related: [hermes-desktop-app, hermes-bootstrap-installer]
---

# Hermes Desktop Does Not Require Sudo

The Hermes Desktop app itself does **not** require `sudo` to run — it installs entirely into `~/.hermes/` (per-user). The Electron app (`main.cjs`) and Tauri bootstrap contain zero calls to elevated privileges.

## Why Sudo Prompts Still Appear

1. **Installing `.deb` or `.rpm` packages** — Package managers inherently need root. **Fix:** Use the **AppImage** instead (`chmod +x ./Hermes-*.AppImage && ./Hermes-*.AppImage`).

2. **Missing `libfuse2` on Arch/Manjaro** — Arch ships `fuse3` by default; AppImages need `fuse2`. **Fix:**
   ```bash
   sudo pacman -S fuse2
   ```

3. **Agent's terminal tool runs `sudo` commands** — The AI agent inside Hermes may execute `sudo` commands during its work. That's the agent's behavior, not the desktop shell.

4. **First-launch bootstrap** — If a system dependency (e.g., `python3.11`) is missing, the installer may invoke the system package manager, triggering a sudo prompt.

## Verdict

Use the AppImage on Linux, ensure `fuse2` is installed, and you'll see no sudo prompts from the desktop app itself. Any sudo prompts mid-session are from the agent's shell commands.
