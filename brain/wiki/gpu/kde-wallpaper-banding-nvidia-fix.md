---
source_session: "20260425_200239_b9aadb"
category: gpu
tags: [kde, plasma, wallpaper, banding, nvidia, wayland, kwin]
---

# KDE Wallpaper Banding Fix (NVIDIA Wayland)

Color banding in desktop wallpapers on KDE Plasma 6 / Wayland / NVIDIA can stem from JPEG compression, video wallpaper plugins, or kwin compositor scaling.

## Diagnosing

- JPEG wallpapers introduce 8-bit compression artifacts in gradients
- Video wallpaper plugins (`smart.video.wallpaper.reborn`) render mp4 at low quality on Wayland/NVIDIA
- kwin's default `ScalingMethod` may be `Accurate` but not always applied

## Fixes (in order of impact)

1. **Convert JPGs to PNG** — lossless, eliminates compression banding:
   ```bash
   convert input.jpg output.png
   ```

2. **kwinrc compositor tweaks** — edit `~/.config/kwinrc`:
   ```ini
   [Compositing]
   ScalingMethod=Accurate
   ColorCorrect=true
   LatentPolicy=HighQuality
   ```
   Then `qdbus org.kde.KWin /KWin reconfigure` or logout.

3. **NVIDIA 10-bit color** — force higher bit depth per monitor:
   ```bash
   nvidia-settings --assign CurrentMetaMode="DP-4: 3440x1440_144 { ForceCompositionPipeline=On, pixdepth=10 }"
   ```

4. **NVIDIA dithering**:
   ```bash
   nvidia-settings -a [GPU:0]/Dithering=0
   ```

5. **Verify NVIDIA DRM modeset**:
   ```bash
   cat /sys/module/nvidia_drm/parameters/modeset   # must be "Y"
   ```

Related: [[kwin-wayland-latency-patches-165hz]], [[kwin-nvidia-wayland-gl2-compositor]], [[nvidia-595-grub-modprobe-env-kwin-config]]
