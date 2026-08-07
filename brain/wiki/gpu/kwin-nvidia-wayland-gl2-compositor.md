---
source_session: "20260502_150358_5e17d2"
date: "2026-07-13"
category: gpu
tags: [nvidia, kwin, wayland, compositor, gl2, opengl, kde]
---

# KWin NVIDIA Wayland gl2 Compositor Fallback

On NVIDIA Wayland with the 595 driver branch, KWin reports `compositingType = gl2` regardless of the configured backend, even though the NVIDIA driver exposes OpenGL 4.6.0 via EGL.

## Cause

The `gl2` label is KWin's **runtime fallback** when using EGL on Wayland — it's not a driver capability limitation. NVIDIA's EGL implementation on Wayland doesn't expose OpenGL 3.x/4.x context properly through GBM, so KWin falls back to `gl2` at runtime irrespective of `Backend=gl4` in `kwinrc`.

## Workaround: Force OpenGL ES (O2ES)

Set the env var `KWIN_COMPOSE=O2ES` to force KWin to use OpenGL ES instead of Desktop OpenGL:

```bash
mkdir -p ~/.config/plasma-workspace/env
echo 'export KWIN_COMPOSE=O2ES' > ~/.config/plasma-workspace/env/kwin-opengl.sh
chmod +x ~/.config/plasma-workspace/env/kwin-opengl.sh
```

This requires a **logout and login** — setting it in an interactive shell has no effect because KWin is already running.

## Future

KDE Plasma 6.8 is dropping Desktop OpenGL entirely in favor of OpenGL ES (`O2ES`), making this issue obsolete.

## Related

- [[nvidia-595-grub-modprobe-env-kwin-config]] — KWin NVIDIA config
- [[kwin-wayland-latency-patches-165hz]] — KWin latency tuning
- [[nvidia-wayland-kwin-latency-policy]] — KWin latency policy
