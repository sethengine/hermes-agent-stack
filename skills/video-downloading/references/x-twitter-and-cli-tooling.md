# X/Twitter downloads & pip vs pipx — session detail

Context: user asked to download an X post video, then to learn how to run yt-dlp
from zsh, then asked for a comprehensive pip vs pipx explanation.

## X/Twitter download behavior (observed, 2026-08)

- yt-dlp resolves `https://x.com/user/status/<id>` fine WITHOUT the `/video/1`
  suffix. The suffix refers to the same media object; using the bare post URL is
  the reliable pattern and matches what users paste.
- Works without login: yt-dlp requests a fresh guest token per run. If you hit an
  auth/rate-limit error, re-running usually succeeds — do not jump to cookies.
- X serves HLS: hundreds/thousands of tiny fragments (`Total fragments: 848`,
  `1569`, etc.). Progress output is ~1MB of `\r`-overwritten lines even for a
  40-minute clip. Always pass `--no-progress` in agent/non-interactive runs.
- Final step merges video + audio into one mp4 and deletes the intermediate
  fragment files ("[Merger] Merging formats into ...mp4").
- Output sizes scale with duration: 42min ≈ 169MB, 1h18 ≈ 380MB at 720p.
- Verify with `ffprobe` duration: the Stanford "1 hour course" clip came back
  `duration=4708s` (~78min incl. credits) — sanity-check against post claims.

## pip vs pipx — the decision (end-user framing)

| | pip | pipx |
|---|---|---|
| What it installs | libraries your code `import`s | commands you `run` from the terminal |
| Isolation | none beyond the active venv | one venv per app under `~/.local/share/pipx/venvs/` |
| PATH artifact | scripts in env's bin/ | symlink in `~/.local/bin` |
| Upgrade | `pip install -U pkg` | `pipx upgrade pkg` |
| List | `pip list` | `pipx list` |

Workflow:
- CLI tools you run → `pipx install yt-dlp`, `pipx install ruff`, etc.
- Libraries for projects → `python -m venv .venv && source .venv/bin/activate && pip install ...`
- pipx one-offs: `pipx run <pkg>` (ephemeral), `pipx inject <app> <dep>`,
  `pipx runpip <app> ...`, `pipx ensurepath`.

Common mistakes: `sudo pip install` (corrupts system Python), `pip install --user`
for project deps (no isolation), pipx for importable libraries (not importable).

Note: installing `yt-dlp` with plain pip into an existing isolated venv (e.g. a
tooling venv) is acceptable; pipx is the cleaner default on a personal machine.
