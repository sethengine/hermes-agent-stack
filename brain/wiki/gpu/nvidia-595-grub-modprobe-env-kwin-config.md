---
source: "20260710_212706_69a41c"
date: "2026-07-10T19:06:43+00:00"
category: "gpu"
related: ["gamescope-hdr-kde-wayland-nvidia", "nvidia-wayland-kwin-latency-policy", "nvidia-595-bugs"]
---

# NVIDIA 595 GRUB, Modprobe, Env, and KWin Config for KDE Wayland

The last30days research on KDE Wayland NVIDIA optimization produced a comprehensive config set for NVIDIA 595 on KDE Wayland with RTX 5060 Ti.

## GRUB Parameters

Add to `GRUB_CMDLINE_LINUX_DEFAULT`:

```
nvidia_drm.modeset=1 nvidia_drm.fbdev=1 nvidia.NVreg_EnableGpuFirmware=0
```

`nvidia_drm.modeset=1` is required for Wayland. `NVreg_EnableGpuFirmware=0` eliminates GSP firmware micro-stutter and suspend/resume crashes — the root cause of many 595-series bugs.

## Modprobe (`/etc/modprobe.d/nvidia.conf`)

```
options nvidia NVreg_PreserveVideoMemoryAllocations=1 NVreg_TemporaryFilePath=/var/tmp
options nvidia NVreg_RegistryDwords="PowerMizerEnable=0x1;PerfLevelSrc=0x2222;PowerMizerLevel=0x3"
options nvidia-drm modeset=1 fbdev=1
```

PowerMizer fixes: `PowerMizerLevel=0x3` forces max performance to eliminate clock-ramp latency on 165Hz displays (~10-15W extra idle power trade-off).

## Environment Variables (`~/.config/environment.d/nvidia.conf`)

```
KWIN_DRM_NO_AMS=1              # Disable atomic mode setting for multi-monitor stutter
__GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1  # Skip shader cache purge on boot
__GL_THREADED_OPTIMIZATIONS=1          # Offload GL calls to worker thread
```

## KWin Compositing (`~/.config/kwinrc`)

```
[Compositing]
GLPreferBufferSwap=0           # Prefer mailbox/async swap on NVIDIA
WindowsBlockCompositing=false  # Prevent un-redirect stutter
```

References: [[kwin-wayland-latency-patches-165hz]], [[gamescope-nvidia-595-proton11-d2r-config]]
