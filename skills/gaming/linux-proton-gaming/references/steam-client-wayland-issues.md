# Steam Client: NVIDIA Wayland Rendering Issues

## Configuration

- **GPU**: RTX 5060 Ti (NVIDIA driver 595.71.05)
- **Display**: KDE Plasma 6.5.6 Wayland, 3440×1440@165Hz
- **Steam**: 1.0.0.85-7 (native package, Manjaro)
- **KWin compositor**: OFF (disabled for game latency)

## Diagnosis Evidence

From `~/.steam/steam/logs/webhelper_gpu.txt`:

```
gpu_compositing: disabled_software
disabled via blocklist, about:flags or the command line.
Skipping nVidia device named: nvidia-drm
```

All `gpuMemoryBufferInfo` entries show `Software only` — every format (RGBA, BGRA, YUV, P010) is CPU-only.

VAAPI warning (`Skipping nVidia device named: nvidia-drm`) is cosmetic — VAAPI doesn't support NVIDIA. Unrelated to compositing.

### Root cause

CEF (Chromium Embedded Framework) that powers Steam's web views has an NVIDIA blocklist active on Wayland. The Chromium GPU process initializes, detects Wayland + NVIDIA, and disables GPU compositing `k_EBrowserGPUStatus_DisabledCommandLine`.

## The Catch-22

| GPU accel setting | Problem |
|---|---|
| ON | Flickering, artifacts, corrupted menus — CEF + XWayland + NVIDIA compositor interaction bug. Resizing window temporarily fixes it. |
| OFF | ~1fps UI at 3440×1440 — CPU-only rendering of entire web view stack. Big Picture is unusable. |

## Error -379: GPU IPC Corruption Path

When GPU accelerated rendering is ON but Error -379 ("Failed to load web page") appears, the root cause can be GPU→renderer IPC corruption over XWayland rather than a network/HTTP error.

**Log evidence** (`~/.local/share/Steam/logs/cef_log.txt`):

```
ERROR:bad_message.cc(29)] Terminating renderer for bad IPC message, reason 213
ERROR:zygote_communication_linux.cc(292)] Failed to send GetTerminationStatus message to zygote
```

Chromium (Chrome 126, as bundled by Steam CEF) checks IPC message integrity between the GPU process and renderer process. When NVIDIA's XWayland translation corrupts the IPC payload, Chromium terminates the renderer. The web view goes black (no page loaded) and Error -379 is shown.

This is distinct from the HTTP-response-code-failure -379 documented in the cloud sync troubleshooting — same error code, different root cause chain.

**X error stream** accompanying the corruption:

```
WARNING:connection.cc(56)] X error received.  Request: SendEventRequest, Error: WindowError{...}
```

Multiple `SendEventRequest` WindowErrors indicate X11 events failing to route through XWayland, which cascades into CEF IPC corruption.

**gpu_compositing status when this happens**: `enabled` — GPU compositing IS active, but the IPC channel is unreliable.

### Fixes for IPC corruption path

1. **`STEAM_FORCE_WAYLAND=1`** — makes Steam connect as a native Wayland client, bypassing XWayland entirely. The GPU→renderer IPC goes through proper Wayland paths.
2. **gamescope wrapper** — runs Steam inside gamescope, which provides its own XWayland/compositing environment that handles the IPC correctly:
   ```sh
   gamescope -w 3440 -h 1440 -- steam
   ```
3. **gamescope wrapper (reliable fix)** — runs Steam inside gamescope, which provides its own X11 compositing environment:
   ```sh
   gamescope -w 3440 -h 1440 -- steam
   ```
4. **KWin compositor enabled** — `qdbus org.kde.KWin /Compositor resume` before launch. The compositor provides the missing XWayland composition layer that NVIDIA's driver expects.

## Desktop Entry Wrapper Pattern

The proven persistent fix combines gamescope + KWin compositor toggle:

```bash
#!/bin/bash
# ~/.local/bin/steam-wrapper
qdbus org.kde.KWin /Compositor resume 2>/dev/null
gamescope -w 3440 -h 1440 -- steam "$@"
sleep 2
qdbus org.kde.KWin /Compositor suspend 2>/dev/null
```

Set desktop entry to `/usr/share/applications/steam.desktop`:
```
Exec=/home/user/.local/bin/steam-wrapper %U
```

## Placebo Warning: STEAM_FORCE_WAYLAND

`STEAM_FORCE_WAYLAND=1` is **not handled** by Steam's launch scripts. Grepping `steam.sh` and `steamwebhelper.sh` for `STEAM_FORCE_WAYLAND` returns nothing. The env var has no effect on the Steam client's display backend — it is neither read nor forwarded. Do not recommend it. Use gamescope instead (above).

## Additional Diagnostic: "Cannot Connect to Internet"

When GPU→renderer IPC corruption causes web views to fail, the Steam UI displays what looks like a network connectivity error. The store and library pages show blank or error states. However, actual network connectivity is intact:

- `curl -sI https://store.steampowered.com` returns HTTP 200
- Steam downloads manifests: `Downloading manifest: https://client-update.fastly.steamstatic.com/steam_client_ubuntu12`
- SteamID is set: `SteamInternal_SetMinidumpSteamID: Setting Steam ID: 7656119...`

This is a **rendering failure, not a network failure**. The CEF renderer was terminated (bad IPC message), so it can't display web content. The user sees an empty/broken store page and interprets it as no internet.

1. Launch Steam on KDE Wayland + NVIDIA
2. Open Store or Library tab
3. If GPU accel OFF: sluggish scrolling, slow response, single-digit FPS
4. If GPU accel ON: flickering rendering, corrupted right-click menus, visual artifacts

## Workarounds Validated

1. **`steam -ignore-gpu-blocklist -enable-gpu-rasterization`** — forces GPU compositing past CEF blocklist
2. **KWin compositor ON for Steam** — `kwinctrl set compositing on` before launch; handles XWayland composition properly
3. **Window resize** — quick fix when artifacts appear with GPU accel ON
4. **`STEAM_FORCE_WAYLAND=1`** — experimental native Wayland path for Steam (avoids XWayland)

## Upstream References

- https://github.com/ValveSoftware/steam-for-linux/issues/10313 — Store flicker on NVIDIA Wayland
- https://github.com/ValveSoftware/steam-for-linux/issues/10537 — Corrupted right-click menus
- https://github.com/ValveSoftware/steam-for-linux/issues/13151 — GPU accel defaults to OFF (May 2026)
- https://forums.developer.nvidia.com/t/550-wayland-steam-has-glitches-when-launched-with-gpu-accelerated-rendering/290157
- https://steamcommunity.com/groups/SteamClientBeta/discussions/0/4697909557442180251/ — Context menu display issue
- https://wiki.archlinux.org/title/Steam/Troubleshooting — Steam flicker/blink section

## Not Related

- `Skipping nVidia device named: nvidia-drm` in VAAPI log — NVIDIA doesn't use VAAPI; this warning is harmless
- `PROTON_ENABLE_WAYLAND=0` — affects games, not the Steam client's own rendering
