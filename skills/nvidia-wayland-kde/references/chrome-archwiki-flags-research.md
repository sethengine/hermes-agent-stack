# Chrome Flag Configuration — ArchWiki Research

**Date:** 2026-07-17
**Context:** Deep-research + last30days passes for Chrome flag configuration on RTX 5060 Ti + Ultra 7 265K + KDE Wayland + NVIDIA 595.71.05 + Chrome 149.

## Key Sources

- [ArchWiki: Chromium](https://wiki.archlinux.org/title/Chromium) — last edited 2026-06-29
- [ArchWiki: NVIDIA](https://wiki.archlinux.org/title/NVIDIA) — last edited 2026-06-12

## Authoritative Flag Documentation

### Making Flags Persistent

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Making_flags_persistent):

> You can put your flags in a `chromium-flags.conf` file under `$HOME/.config/`
> Flags are defined as if they were written in a terminal. Lines starting with `#` are skipped.

Note: The Arch-specific wrapper at `/usr/bin/google-chrome-stable` reads `~/.config/chrome-flags.conf` (note: `chrome-` not `chromium-`). The Chromium package uses `chromium-flags.conf`.

### Hardware Video Acceleration

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Hardware_video_acceleration):

> Since Chromium 143, hardware acceleration via VA-API should work out of box. [User is on Chrome 149]
>
> When using EGL/Wayland and Chromium versions prior to 143, using `AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL` may improve performance. [@149, ZeroCopyGL is optional/pre-143 optimization]
>
> For proprietary NVIDIA support, install `libva-nvidia-driver` and append the `VaapiOnNvidiaGPUs` feature.
>
> To use the system GL renderer on Xorg or Wayland, use `--use-gl=egl`.

Note: Despite the wiki saying `--use-gl=egl` is the system GL renderer, on Chrome 149 + NVIDIA 595 + Wayland, `--use-gl=egl` causes GPU process failure ("GPU was unable to boot"). The only working path is `--use-gl=angle`.

### Force GPU Acceleration

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Force_GPU_acceleration):

> `--ignore-gpu-blocklist`
> `--enable-zero-copy`

### Autoscroll (MiddleClickAutoscroll)

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Enabling_autoscroll_with_middle_mouse_button):

> To enable this feature, launch your browser with the `--enable-features=MiddleClickAutoscroll` flag.
>
> While setting `--enable-blink-features` works the same way, the browser displays a "stability and security will suffer" warning.

### Running on Xwayland (NVIDIA crash workaround)

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Running_on_Xwayland):

> If you are using NVIDIA's proprietary driver, running Chromium on Xwayland may cause the GPU process to occasionally crash.
> To prevent the GPU process from crashing, add: `--use-angle=vulkan --use-cmd-decoder=passthrough`

Note: `--use-angle=vulkan` does NOT work on native Wayland — it fails with "'--ozone-platform=wayland' is not compatible with Vulkan" on NVIDIA. The Xwayland workaround only applies on X11/Xwayland sessions.

### 165Hz Display

From [ArchWiki/Chromium](https://wiki.archlinux.org/title/Chromium#Running_on_the_Wayland_backend):

> Plasma 6 makes Chromium work flawlessly on high refresh rates.
> Mixed refresh rates workaround: `--use-gl=egl --ignore-gpu-blocklist --enable-gpu-rasterization`

## Tested Configurations

| Config | Network | YouTube Sync | VA-API HW Decode | Autoscroll |
|--------|---------|-------------|-----------------|------------|
| `--use-angle=gl --use-gl=angle` + ZeroCopyGL | ❌ Crashes | ❌ Desync | ✅ Works | ❌ Missing flag |
| `--use-gl=angle` + ZeroCopyGL (no `--use-angle=gl`) | ✅ Works | ❌ Desync | ✅ Works | ❌ Missing flag |
| `--use-gl=angle` (no ZeroCopyGL) | ✅ Works | ✅ Sync | ✅ Works | ❌ Missing flag |
| `--use-gl=angle` + `MiddleClickAutoscroll` (no ZeroCopyGL) | ✅ Works | ✅ Sync | ✅ Works | ✅ Works |
| `--use-gl=egl` alone | ❌ GPU fails to boot | — | — | — |

## Recommended Config (Tested Working)

```
--ozone-platform=wayland
--use-gl=angle
--ignore-gpu-blocklist
--enable-gpu-rasterization
--enable-native-gpu-memory-buffers
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL,UseMultiPlaneFormatForHardwareVideo,MiddleClickAutoscroll
```

## Key Findings

1. `--enable-blink-features` triggers security warning; use `--enable-features` instead
2. ZeroCopyGL causes YouTube desync on NVIDIA Wayland — drop it
3. `--use-angle=gl` (explicit GL backend for ANGLE) crashes GPU process on Wayland — omit it
4. `--use-gl=egl` (native EGL, no ANGLE) fails on Chrome 149 + NVIDIA 595 — stick with `--use-gl=angle`
5. `--enable-features=MiddleClickAutoscroll` works without warning when in `--enable-features` (not `--enable-blink-features`)
6. Chrome updates do NOT overwrite `~/.config/chrome-flags.conf` — this is the safest place for flags
