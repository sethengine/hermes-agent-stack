---
source_session: 20260731_183614_9bd2b1
date: 2026-07-31
category: software
title: Chrome ANGLE gl-egl (negative frame latency) vs vulkan (breaks NVDEC) tradeoff
---

# Chrome `--use-angle` backend tradeoff on NVIDIA Wayland

Two opposing symptoms depending on which ANGLE backend Chrome uses. Pick per workload — they cannot both be satisfied.

## Problem A — `--use-angle=gl-egl`: display timing corruption
On NVIDIA + Wayland, `gl-egl` makes Chrome log **"Frame latency is negative"** (e.g. `-0.103 ms`, repeatedly). The display compositor presents frames before they're ready → desktop feels laggy/janky and keeps `kwin_wayland` pegged on screen damage.

Session recommendation was to switch to vulkan:
```bash
sed -i 's/--use-angle=gl-egl/--use-angle=vulkan/' ~/.config/chrome-flags.conf
# restart Chrome; journalctl --since '-5 min' | grep -c 'Frame latency is negative' → 0
```

## Problem B — `--use-angle=vulkan`: breaks video decode
Per [[chrome-angle-gl-nvidia-r595-gpu-crash]], `--use-angle=vulkan` is **incompatible** with `nvidia-vaapi-driver` for NVDEC/VA-API — video decode acceleration is lost (YouTube/streaming desync or no HW decode).

## Resolution
- **Gaming / desktop latency priority:** use `vulkan` (fixes negative-latency jank). Accept software/non-NVDEC video decode.
- **Streaming / YouTube priority:** keep `gl-egl` (or `--use-gl=egl`) for NVDEC; tolerate the display-timing errors.
- This conflict is the reason there is no single "correct" Chrome flags file — the choice is workload-dependent.

Related: [[chrome-angle-gl-nvidia-r595-gpu-crash]], [[nvidia-wayland-vrr-input-lag-kwin]], [[chrome-hw-video-accel-nvidia-wayland]]
