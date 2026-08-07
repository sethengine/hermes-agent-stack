---
source_session: 20260712_182512_850b41
date: 2026-07-13
category: software
tags: [steam, cef, gamescope, nvidia, wayland, xwayland, ipc, error-379, chromium]
---

# Steam CEF IPC Corruption on NVIDIA Wayland

## Problem

Steam web views (store, library, cloud sync) fail with Error -379 (`ERR_HTTP_RESPONSE_CODE_FAILURE`) on NVIDIA + KDE Wayland. Web pages render as black squares.

## Root Cause

CEF's GPU and renderer processes exchange IPC messages over XWayland. NVIDIA's driver corrupts these messages:

```
ERROR:bad_message.cc(29)] Terminating renderer for bad IPC message, reason 213
```

Chromium kills the renderer when it receives corrupted IPC, producing black squares. Steam forces `--disable-gpu-compositing --disable-gpu` on NVIDIA Wayland in its launch scripts; even when GPU compositing is enabled in settings, the IPC corruption persists.

## Fix — Gamescope Wrapper

Run Steam inside gamescope to bypass the host XWayland:

```bash
#!/bin/bash
qdbus org.kde.KWin /Compositor resume
gamescope -- steam "$@"
sleep 2
qdbus org.kde.KWin /Compositor suspend
```

- gamescope creates a clean X11 environment for Steam, isolating CEF from the host XWayland
- CEF web views render properly without IPC corruption
- KWin compositor toggles on/off around the session (fixes XWayland rendering artifacts)

## Desktop Entry

Update `/usr/share/applications/steam.desktop` to use the wrapper:

```
Exec=/home/sethengine/.local/bin/steam-wrapper %U
```

## Related

- [[steam-nvidia-wayland-rendering]] — rendering artifacts with GPU compositing
- [[gamescope-xwayland-overhead]] — gamescope latency considerations
- [[nvidia-wayland-hardware-cursors]]
