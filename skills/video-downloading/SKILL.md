---
name: video-downloading
description: "Download videos from social sources with yt-dlp."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Video, Download, yt-dlp, Twitter, X, YouTube, CLI, pipx]
---

# Video Downloading (yt-dlp)

Pull video files from X/Twitter, YouTube, TikTok, Vimeo, etc. into local files,
and keep your CLI tooling clean (pip vs pipx decision).

## Install (one time)

```bash
pip3 install yt-dlp          # fine inside an existing venv (isolated)
pipx install yt-dlp          # preferred on a personal machine: isolated CLI on PATH
```
Update before downloads — X/Twitter auth changes often:
```bash
pip3 install -U yt-dlp   # or pipx upgrade yt-dlp
```
After `pipx install`, ensure `~/.local/bin` is on `PATH` (`pipx ensurepath` or add to `~/.zshrc`).

## Core workflow

```bash
cd ~/Downloads
yt-dlp -o "name_%(id)s.%(ext)s" "POST_URL"   # explicit, predictable filename
yt-dlp "POST_URL"                            # auto filename
```
yt-dlp auto-detects and merges best video+audio into one `.mp4`.

Always **verify before reporting success**:
```bash
file ~/Downloads/name.mp4     # confirm MP4 Base Media
ffprobe -v error -show_entries format=duration \
  -show_entries stream=codec_name,width,height \
  -of default=noprint_wrappers=1 ~/Downloads/name.mp4   # duration + codecs
```
Sanity-check the duration against what the post claims (a "1 hour course" must show
~3600s+, not 60s) — a multi-thousand-second value is normal for hour-long talks.

## Useful flags

| Flag | Effect |
|------|--------|
| `-o "name.%(ext)s"` | Custom output filename |
| `-F URL` | List available formats, then pick with `-f` |
| `-f "bestvideo+bestaudio"` | Force best quality |
| `-f "bestvideo[height<=480]+bestaudio"` | Cap resolution (smaller file) |
| `-x --audio-format mp3` | Audio-only → mp3 |
| `-a urls.txt` | Batch-download all URLs (one per line) |
| `--no-progress` | Suppress progress spam (important in agent logs — otherwise ~1MB of \r lines) |

## Pitfalls

- **X/Twitter: use the bare post URL** (`https://x.com/user/status/<id>`). The
  `/video/1` suffix points at the same media — dropping it avoids confusion and
  matches how users paste links.
- **No login needed for X** — yt-dlp fetches a fresh guest token each run. On an
  auth/rate-limit error, just re-run; don't reach for cookies immediately.
- **Huge log spam**: X downloads are HLS (hundreds of fragments) and each fragment
  emits a `\r` progress line. Always use `--no-progress` in non-interactive runs,
  or pipe through `tail -40` for the summary lines.
- **`sudo pip install` is never the answer** for CLI tools.

## pip vs pipx (CLI tool installs)

- **pip** = install a *library* your code `import`s — use inside a project venv.
- **pipx** = install a *command* you run from the terminal — each app gets its own
  isolated venv, no dependency collisions with project code.
- Decision rule: you `run` it → pipx. Your code `import`s it → pip in a venv.
- pipx extras: `pipx run <pkg>` (ephemeral one-off), `pipx list`, `pipx upgrade-all`,
  `pipx inject <app> <dep>`, `pipx runpip <app> ...`.

## See also

- `references/x-twitter-and-cli-tooling.md` — session detail on X/Twitter HLS
  download behavior and the pip/pipx decision explained for end users.
