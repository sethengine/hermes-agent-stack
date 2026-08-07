---
source_session: 20260608_200754_8eba19
date: 2026-06-08
category: gpu
tags: [chrome, nvidia, wayland, va-api, video-decode, nvdec]
---

# Chrome HW Video Acceleration on NVIDIA Wayland

## System Requirements

- **Chrome/Chromium 149+** with `--enable-features=VaapiOnNvidiaGPUs`
- **nvidia-utils 595.71.05+** with `libva-nvidia-driver` (NVDEC VA-API backend)
- **`vainfo`** should list all codecs as available

## Chrome Flags (`~/.config/chrome-flags.conf`)

```
--ozone-platform=wayland
--use-gl=angle
--ignore-gpu-blocklist
--enable-gpu-rasterization
--enable-native-gpu-memory-buffers
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks
--disable-features=UseChromeOSDirectVideoDecoder
```

Two VA-API backends are available:
1. **nvidia (direct backend)** — All codecs, standard NVDEC
2. **nvidia_vulkan** — H264/HEVC/VP9/AV1 only (prototype, 0.1.0)

## Caveat

HW video decode on NVIDIA Blackwell can trigger Xid 31 MMU faults from Chrome NVDEC0, causing input lag. See [[chrome-nvdec-xid31-input-latency]].

[[chrome-angle-nvidia-wayland-latency]] [[chrome-flags-conf]]
