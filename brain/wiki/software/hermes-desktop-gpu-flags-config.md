---
source: "20260717_210456_54b430"
date: "2026-07-26"
category: "software"
tags: [hermes, electron, gpu, opengl-es, wayland, angle, performance, flags]
wiki-links: [hermes_desktop_app_cpu_optimizations, chrome_angle_nvidia_wayland_latency]
---

# Hermes Desktop GPU Flags Configuration

Electron GPU acceleration flags for Hermes Desktop on KDE Wayland + NVIDIA.

## ⚠️ Correction: `--use-gl=angle` Kills GPU on Hermes

**ANGLE/GL-EGL flags can DESTROY GPU acceleration.** On Hermes Desktop (Electron), `--use-gl=angle --use-angle=gl-egl` prevents the GPU process from starting entirely — resulting in **pure CPU software rendering** with no GPU process visible.

Tested on: NVIDIA 610.43.03, KDE Wayland, RTX 5060 Ti:
- **With** `--use-gl=angle`: ❌ No GPU process, CPU-only rendering
- **Without** those flags: ✅ GPU process starts, hardware acceleration works

If you notice poor performance, verify the GPU process exists:
```bash
ps aux | grep "[H]ermes" | grep "type=gpu"
```
If missing, remove the ANGLE flags and let Electron use its defaults.

OpenCode (no ANGLE flags) had a working GPU process from the start — confirming the flags are the culprit.

## Configuration (`~/.hermes/config.yaml`)

```yaml
desktop:
  electron_flags:
    --ozone-platform=wayland          # Native Wayland (no X11 translation)
    --use-gl=angle                    # ANGLE rendering
    --use-angle=gl-egl               # GL-EGL (matches Chrome config)
    --ignore-gpu-blocklist            # Bypass driver blocklist
    --enable-gpu-rasterization        # GPU rasterization
    --enable-native-gpu-memory-buffers # GBM/dma-buf
    --enable-zero-copy                # Buffer sharing w/o copies
    --enable-oop-rasterization        # Out-of-process raster
    --canvas-oop-rasterization        # Canvas off main thread
    --enable-raw-draw                 # Raw draw path
    --enable-hardware-overlays        # Hardware overlay planes
    --disable-renderer-backgrounding  # No background throttling
    --enable-features=VaapiOnNvidiaGPUs,...  # HW video decode
  disable_gpu: false                  # GPU always on
```

## Verification

```bash
# Confirm flags on GPU process
ps aux | grep "[H]ermes" | grep "type=gpu" | tr ' ' '\n' | grep -E 'enable|disable|ozone|angle'
# GPU utilization
nvidia-smi dmon -s u -d 2
```

Requires full restart (`hermes desktop`). Flags are parsed at Electron startup.

## Related
- [[hermes_desktop_app_cpu_optimizations]]
- [[chrome_angle_nvidia_wayland_latency]]
