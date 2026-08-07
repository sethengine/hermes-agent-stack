# Steam NVIDIA Wayland Rendering Issues

**source:** session `20260712_182512_850b41` (2026-07-12)
**category:** software
**tags:** [steam, nvidia, wayland, xwayland, rendering, artifacts, gpu-compositing, kwin]

## Problem

Steam client is slow and has rendering artifacts on NVIDIA + KDE Wayland. GPU compositing in Steam's embedded Chromium/CEF web views is disabled, forcing software rendering at 3440×1440.

## Diagnosis

Check Steam's web helper GPU status:

```
gpu_compositing: disabled_software
Gpu compositing has been disabled, either via blocklist, about:flags or the command line.
Skipping nVidia device named: nvidia-drm
```

This is a known NVIDIA + Wayland XWayland issue: flipping GPU compositing ON in Steam settings causes flickering artifacts.

## Workarounds

### Option 1: Force GPU acceleration past blocklist

Enable in Steam → Settings → Interface → "Enable GPU accelerated rendering in web views" → ON

Then launch Steam with:
```sh
steam -ignore-gpu-blocklist -enable-gpu-rasterization
```

This forces CEF/Chromium to use the GPU even when NVIDIA is blocklisted for compositing on Wayland. Driver 595.x handles this better than older drivers.

### Option 2: Window resize workaround

If flickering persists with Option 1, resize the Steam window to force a re-render that clears artifacts.

### Option 3: Toggle KWin compositor wrapper

Since KWin compositor is typically disabled for game latency (`kwinrc → Compositing → Enabled=false`), use a wrapper script that re-enables it for Steam:

```sh
#!/bin/bash
kwinctrl set compositing on
steam "$@"
kwinctrl set compositing off
```

### Option 4: Native Wayland mode (experimental)

```sh
STEAM_FORCE_WAYLAND=1 steam
```

### Option 5: Performance mitigations (GPU accel OFF)

Create `~/.steam/steam/steam_dev.cfg`:
```
@nClientDownloadEnableHTTP2PlatformLinux 0
unShaderBackgroundProcessingThreads 6
```

## References

- ValveSoftware/steam-for-linux issue [#10313](https://github.com/ValveSoftware/steam-for-linux/issues/10313)
- ValveSoftware/steam-for-linux issue [#13151](https://github.com/ValveSoftware/steam-for-linux/issues/13151)
