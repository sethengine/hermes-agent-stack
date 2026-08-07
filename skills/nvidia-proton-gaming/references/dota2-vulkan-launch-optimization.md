# Dota 2 Vulkan Launch Optimization (CPU/GPU Imbalance)

## Symptoms

- Severe CPU/GPU imbalance: ~285% CPU utilization / ~8% GPU utilization
- Game feels sluggish despite decent FPS
- Frame-pacing uneven (CPU-bound pipeline stalls)

## Root Cause

Dota 2's default launch behavior under Vulkan + Proton + NVIDIA Wayland creates a pipeline bottleneck where the CPU driver thread saturates while the GPU waits on presentation semaphores. The game's default Hammer/Panorama UI compositing also consumes rendering resources for unnecessary UI elements.

## Fix: Launch Options

Add these to Steam → Dota 2 → Properties → Launch Options:

```
-vulkan -high -novid +@panorama_min_comp_layer_dimension 0 -prewarm_panorama %command%
```

| Flag | Purpose |
|------|---------|
| `-vulkan` | Force Vulkan renderer (performance > DX11/OpenGL on NVIDIA) |
| `-high` | Set high CPU priority for the Dota 2 process |
| `-novid` | Skip intro video (faster launch) |
| `+@panorama_min_comp_layer_dimension 0` | Reduce Panorama UI compositing layer minimum size — eliminates unnecessary GPU work for off-screen/minimized UI elements |
| `-prewarm_panorama` | Pre-warm the Panorama UI system at launch instead of on first interaction |

## KWin WindowsBlockCompositing

Dota 2's `WindowsBlockCompositing=true` in the KWin window rules may behave differently under Vulkan vs DX11/OpenGL. If the game's launch script or Proton layer doesn't trigger the block rule before the first frame, compositing stays active during the initial loading phase, adding 1-2 frames of input lag.

## irqbalance

Enable irqbalance to spread interrupt load across CPU cores (prevents a single core from handling all audio/input/GPU interrupts during gaming):

```bash
sudo systemctl enable --now irqbalance
```

Verify:
```bash
sudo systemctl status irqbalance
```

## Related

- [KWin Compositing and Input Lag](references/kwin-compositing-input-lag.md) (nvidia-wayland-kde skill)
- [MangoHud FPS Limiting](references/mangohud-fps-limiting-proton.md) (nvidia-proton-gaming skill)
- [CPU/GPU Pipeline Bottleneck Diagnosis](references/gpu-pipeline-bottleneck-diagnosis.md) (nvidia-proton-gaming skill)
- Brain wiki: `software/dota2-vulkan-launch-optimization.md`
