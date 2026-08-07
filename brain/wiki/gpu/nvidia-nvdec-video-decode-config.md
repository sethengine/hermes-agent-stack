---
source: "20260711_190829_979025"
category: gpu
date: 2026-07-11
tags: [nvidia, nvdec, video, decode, nvidia-vaapi-driver, youtube, 4k]
---

# NVIDIA NVDEC Video Decode Configuration

The `nvidia-vaapi-driver` module for NVDEC video decode on Wayland uses environment variables to control decode surface caching.

## Key Variable: `NVD_MAX_DETACHED_BACKING_IMAGES`

Controls how many decoded surface frames are cached for video playback. Values:

| Value | Use Case | VRAM Impact |
|-------|----------|-------------|
| 16 | Default — fine for 720p/1080p | ~192 MB |
| 32 | Good for 4K YouTube (VP9/AV1) | ~384 MB |
| 64 | Generous for 4K + multiple streams | ~768 MB |
| 128 | Overkill for RTX 5060 Ti 16GB | ~1.5 GB |

**Recommended:** 64 for RTX 5060 Ti (16GB VRAM). The byte limit (`NVD_MAX_DETACHED_BACKING_IMAGE_BYTES`) caps total at ~256 MB by default anyway.

## Where to Set

```bash
# Per-session
export NVD_MAX_DETACHED_BACKING_IMAGES=64

# In ~/.profile or ~/.zshrc
echo 'export NVD_MAX_DETACHED_BACKING_IMAGES=64' >> ~/.zshrc
```

## Existing Config Locations

Video decode env vars are set in:
- `~/.config/environment.d/99-nvidia.conf` — `LIBVA_DRIVER_NAME=nvidia`, `NVD_BACKEND=direct`
- `~/.profile` — same vars
- `/etc/libva.conf` — system-wide
