---
source_session: 20260805_175257_a8f78b
date: 2026-08-05
category: software
tags: [yt-dlp, x-twitter, video-download, zsh, pip, pipx]
related: [video-downloading]
---

# yt-dlp for X/Twitter Video Downloads

Download videos from X/Twitter posts (and other sites) with `yt-dlp`.

**Install (one-time):**
```zsh
pip3 install yt-dlp        # or: sudo pacman -S yt-dlp (Manjaro)
pip3 install -U yt-dlp     # keep updated — X/Twitter changes often
```

**Basic usage:**
```zsh
cd ~/Downloads
yt-dlp "https://x.com/user/status/123456789"   # just the post URL works — no /video/1 suffix needed
```
Auto-detects best format and merges video+audio into `.mp4`.

**Useful flags:**
```zsh
yt-dlp -o "myvideo.%(ext)s" "URL"   # custom output filename
yt-dlp -F "URL"                     # list available formats
yt-dlp -f "bestvideo+bestaudio" "URL"  # pick specific quality
```

## pip vs pipx

- **pip** — installs Python *libraries* into an environment (`import` them in code)
- **pipx** — installs Python *CLI applications* in isolated per-app venvs; entry-point binaries symlinked into `~/.local/bin` so you can run them from anywhere

One-liner: `pip` = install a library to `import`; `pipx` = install a command to `run`.
