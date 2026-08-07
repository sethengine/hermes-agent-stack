---
source: "20260717_203150_4ba0e0"
date: "2026-07-17"
category: "software"
tags: [alacritty, opengl-es, gles, renderer, egl, wayland, performance]
wiki-links: [alacritty_config_best_practices, chrome_angle_nvidia_wayland_latency]
---

# Alacritty OpenGL ES Renderer Configuration

Alacritty has two rendering backends: Desktop OpenGL 3.3 Core (`Glsl3`, default) and OpenGL ES 2.0 (`Gles2`/`Gles2Pure`). OpenGL ES is typically faster and more reliable on Wayland + NVIDIA.

## Configuration

In `~/.config/alacritty/alacritty.toml`:

```toml
[debug]
renderer = "Gles2"
prefer_egl = true
```

| Option | Effect | Live Reload |
|--------|--------|-------------|
| `renderer = "Gles2"` | Use OpenGL ES 2.0 shaders | ✅ Yes |
| `prefer_egl = true` | Use EGL display backend (bypasses GLX on X11/XWayland) | ❌ No — requires restart |

`renderer` takes effect immediately with `live_config_reload = true`. `prefer_egl` needs a full Alacritty restart because the display backend is set up once at launch.

## Verification

```bash
alacritty msg get-config | grep -A2 debug
```

## Related
- [[alacritty_config_best_practices]]
- [[chrome_angle_nvidia_wayland_latency]]
