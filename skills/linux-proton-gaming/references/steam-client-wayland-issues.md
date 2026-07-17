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

## Reproduction Steps

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
