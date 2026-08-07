---
source_session: 20260730_202842_a5d02b
date: 2026-07-30
category: software
tags: [dota2, vulkan, launch-options, input-lag, cpu-gpu-imbalance, gaming]
related: [gaming-resource-exhaustion-vs-kernel-latency, nvidia-595-grub-modprobe-env-kwin-config]
---

# Dota 2 Vulkan Launch Options for Input Lag

Dota 2 can exhibit severe CPU/GPU imbalance (285% CPU / 8% GPU) when the renderer auto-detect picks an inefficient path on NVIDIA Wayland. Explicit launch options fix this:

```
-vulkan -high -novid +@panorama_min_comp_layer_dimension 0 -prewarm_panorama
```

- **`-vulkan`** — forces Vulkan renderer explicitly (avoids auto-detection issues)
- **`-high`** — elevates process scheduler priority (reduces scheduling delays)
- **`-novid`** — skips intro video
- **`+@panorama_min_comp_layer_dimension 0`** — disables minimum compositor layer size in Panorama UI (reduces unnecessary overlay rendering)
- **`-prewarm_panorama`** — pre-warms the Panorama UI framework at startup

## Additional mitigating actions

- **KWin `WindowsBlockCompositing=true`** under `[Compositing]` in `~/.config/kwinrc` tells KWin to minimize compositor processing for fullscreen games. Note: the existing NVIDIA config recommends `false` for desktop stability; toggle per use-case.
- **Enable irqbalance** (`sudo systemctl enable --now irqbalance`) for dynamic interrupt distribution under game load.
- **Close heavy browser tabs** while gaming — 9+ GB Chrome usage pushes into zram swap, causing micro-stutter.
