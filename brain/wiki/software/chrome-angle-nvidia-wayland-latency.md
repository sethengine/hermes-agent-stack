---
session: 20260502_150358_5e17d2
date: 2026-07-04
category: software
tags: [chrome, nvidia, wayland, latency, angle, egl, rendering, gpu-pipeline]
---

# Chrome ANGLE → NVIDIA Wayland Rendering Latency

Chrome's default GPU rendering path on Linux uses **ANGLE** (`--use-gl=angle`), which translates OpenGL ES through Vulkan. On NVIDIA Wayland, this adds GPU pipeline latency on every frame.

**Symptom:** System-wide lag (typing, mouse, scrolling) even though:
- CPU is 90% idle
- Swap is 0
- `sched_rt_runtime_us=-1` (correct real-time config)
- Performance governor active
- No sleep/resume events occurred

**Diagnostic test:** Launch Chrome with native EGL instead of ANGLE:

```bash
google-chrome-stable --use-gl=egl --ozone-platform=wayland
```

If lag disappears, the issue is ANGLE → NVIDIA Wayland translation overhead.

**Also check:** Playwright Docker container running headless Chrome (`ms-playwright`) may contribute to GPU pipeline contention. Stop if not needed:

```bash
docker stop $(docker ps -q --filter "name=playwright") 2>/dev/null
```

## Related

- ANGLE translates GL calls through Vulkan → adds a GPU pipeline hop on NVIDIA
- `--use-gl=egl` bypasses ANGLE, uses native EGL → fewer translations → lower latency
- This is distinct from the `--disable-gpu` path (software rendering) — EGL still uses GPU
