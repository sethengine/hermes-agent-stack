---
source: "20260608_001440_375423"
date: 2026-06-13
category: gpu
---

# Vulkan FPS Cap Methods

NVIDIA driver env vars do NOT work for Vulkan — they are API-specific:

| Env Var | Works With |
|---------|-----------|
| `DXVK_FRAME_RATE=N` | DXVK (DX9/10/11→Vulkan) **only** |
| `__GL_FPS_LIMIT=N` | OpenGL **only** |

## Working Methods for Vulkan FPS Caps

### 1. Game engine command (simplest)
TF2 example: `fps_max 156` in console or `autoexec.cfg`

### 2. MangoHud (driver-level, all APIs)
```bash
MANGOHUD_CONFIG=fps_limit=156,no_display mangohud %command%
```
`no_display` hides overlay, just applies the cap.

### 3. Gamescope (compositor-level)
```bash
gamescope -r 156 -- %command%
```

### 4. NVIDIA Vulkan layer (nvidia-utils 595+)
Not exposed via env var yet. MangoHud or Gamescope is the practical approach.

Related: [[nvidia-595-bugs]]
