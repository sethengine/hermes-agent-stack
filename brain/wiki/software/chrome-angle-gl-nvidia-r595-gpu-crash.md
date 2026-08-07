---
session: 20260711_185454_bc366a
date: 2026-07-12
category: software
tags: [chrome, nvidia, r595, wayland, angle, gpu-crash, network-service, va-api, youtube-desync, nvdec]
---

# Chrome `--use-angle=gl` GPU Crash on NVIDIA r595 + Wayland

On NVIDIA r595 driver (595.71.05) with Wayland, Chrome's `--use-angle=gl` flag causes the GPU process to crash. The crash cascades: GPU process death triggers the network service to fail, producing **"network connection interrupted"** on every page.

## Root Cause

ANGLE's GL backend (`--use-angle=gl`) hits a GPU process crash on NVIDIA r595 + Wayland. When the GPU process dies, Chrome's sandbox architecture also kills the network service, making all pages unreachable.

## Fix

Replace `--use-angle=gl` with `--use-angle=gl-egl` in `chrome-flags.conf`:

```
# Before (broken)
--use-angle=gl
--use-gl=angle

# After (working)
--use-angle=gl-egl
--use-gl=angle
```

All other flags stay the same. `--use-angle=gl-egl` uses the same GL backend through EGL, which avoids the crash. Alternatively, bypass ANGLE entirely with `--use-gl=egl` (native EGL path), but this disables ANGLE's translation layer.

## Related: YouTube Desync with VA-API on NVIDIA

When using VA-API/NVDEC video decode on NVIDIA r595, the flag `AcceleratedVideoDecodeLinuxZeroCopyGL` causes YouTube audio sync issues (video lags behind audio). Fix: remove this flag from `--enable-features`.

Symptom: Video plays but audio drifts out of sync within seconds. Only affects VA-API decode path, not software decoding.

## Related: `--use-angle=vulkan` and NVDEC

`--use-angle=vulkan` does NOT cooperate with `nvidia-vaapi-driver` for NVDEC on NVIDIA. Vulkan ANGLE backend and the VA-API driver are incompatible — attempting both produces no video decode acceleration.

## Chrome Flags Summary for NVIDIA r595 + Wayland

| Flag | Status | Issue |
|------|--------|-------|
| `--use-angle=gl` | BROKEN | GPU crash → network service death |
| `--use-angle=gl-egl` | WORKING | Safe alternative |
| `--use-angle=vulkan` | INCOMPATIBLE | Breaks NVDEC/VA-API |
| `--use-gl=egl` | WORKING | Bypasses ANGLE entirely |
| `AcceleratedVideoDecodeLinuxZeroCopyGL` | PROBLEMATIC | YouTube desync with VA-API |

## Related Wiki

- [[Chrome ANGLE → NVIDIA Wayland Rendering Latency]]
- [[NVIDIA NVDEC Video Decode Configuration]]
- [[Chrome Middle-Click Autoscroll on Linux]]
- [[NVIDIA R595 Linux Driver Bugs]]
