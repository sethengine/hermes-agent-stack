# Dota 2 on Linux — NVIDIA + KDE Wayland

## System Context

- **GPU/Driver**: RTX 5060 Ti, NVIDIA 595, KDE Plasma 6 Wayland
- **Proton**: GE-Proton11-1 (via Steam compatibility tool)
- **Steam**: native Manjaro package, Wayland session

## Mouse Cursor Capture Loss

**Symptom:** Cursor escapes to KDE compositor cursor, becomes non-interactive mid-game.

**Root cause:** KWin compositor interferes with SDL relative mouse mode on focus events.

**Fix priority:**

1. `SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0 %command%` — prevents SDL minimize on focus loss
2. Disable Steam overlay (Steam → Dota 2 → Properties)
3. Force exclusive fullscreen: add `-fullscreen -window_mode exclusive`
4. Alt+Enter ×2 to reinit mouse confinement mid-game

See `SKILL.md#game-input-issues-on-kde-wayland` for full details.

## Steam Cloud Sync — Error -379

**Symptom:** `Error Code: -379 — Failed to load web page (unknown error)` on launch. Cloud sync fails.

**Meaning:** Chromium `ERR_HTTP_RESPONSE_CODE_FAILURE` — CEF got a non-2xx response from Valve's cloud sync API.

**Fix priority:**

1. `rm -rf ~/.steam/steam/steamapps/compatdata/0/` — bugged Proton prefix
2. Clear `~/.steam/steam/appcache/*`
3. Toggle Steam Beta/Stable

See `references/steam-cloud-sync-error-379.md` and `SKILL.md#steam-cloud-sync-errors-cef-web-layer`.

## Launch Options (cumulative)

```
SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0 mangohud %command% -fullscreen -window_mode exclusive
```

## Graphics Notes

- Prefers DLAA over DLSS (native resolution + temporal AA)
- Frame cap via MangoHud `fps_limit=165` (matches 165Hz display)
