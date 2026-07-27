# NVIDIA 610.43.02 Linux Driver — What's New

**Release date:** May 26, 2026
**Branch:** New Feature (succeeds R595)
**Type:** Feature branch (not Production/stable)
**Availability:** Manjaro `extra` repo (`nvidia-dkms 610.43.02-2`, `nvidia-open-dkms 610.43.02-2`)

## Key New Features

### DRM Color Pipeline API (HDR Offloading)
The biggest change for Wayland. The `nvidia-drm` kernel module now supports the per-plane DRM color pipeline API (Linux 6.19+). Wayland compositors can offload color management (HDR, color space conversion) to NVIDIA display hardware via the upstream `COLOR_PIPELINE` plane property, instead of NVIDIA's proprietary color properties.

**Caveat:** Some Wayland compositors may not correctly handle non-bypassable colorops, causing a blank screen when enabling system HDR. A new `color_pipeline` kernel module parameter for nvidia-drm can disable this feature as a workaround.

### FP16 EGL Framebuffer Configurations on Wayland
Higher precision color in the EGL/Wayland rendering path. Relevant for HDR and color-critical applications.

### DRM Format Modifiers for Multiplanar YCbCr Formats
Better video buffer sharing between components (directly relevant to Chrome/VAAPI video rendering).

### mmap on DMABUF File Descriptors from Discrete NVIDIA GPUs
Allows direct CPU access to GPU-allocated DMABUFs. Important for video encode/decode pipelines.

## Vulkan Changes

### New Extensions
- `VK_EXT_shader_long_vector` — Longer vector support in shaders
- `VK_KHR_internally_synchronized_queues` — Queue synchronization
- `VK_NV_push_constant_bank` — NVIDIA-specific push constant improvement
- `VK_KHR_device_group_creation` — Create Vulkan logical devices from multiple physical devices (opt-in via `__VK_ENABLE_DEVICE_GROUPS=1`)

### Performance Fixes
- Fixed Vulkan performance regression in Doom: The Dark Ages (introduced in 590 series)
- Improved performance in Starfield

## Removals
- **Xinerama support removed** from the NVIDIA X11 driver. Legacy protocol from the 1990s — Wayland/XRandR unaffected.

## Bug Fixes
- Fixed regression from 580.65.06 where some mode timings (e.g. 1920x1080@75) were unavailable

## What's NOT Fixed

| Issue | Status in 610 |
|-------|--------------|
| GSP firmware crash on RTX 5060 Ti (Blackwell) | **Not mentioned in release notes** — no GSP-related fixes listed |
| Chrome video banding / vaPutSurface quality | **Not addressed** — no VAAPI rendering path changes |
| PCIe Gen 5 stability on RTX 50-series | **Not mentioned** |

## Community Reception

- **r/linux_gaming** ([thread](https://www.reddit.com/r/linux_gaming/comments/1to7tnn/nvidia_driver_6104302_released_with_drm_color/)): 463 upvotes, 137 comments. Generally positive about DRM color pipeline and Vulkan improvements. Some concern about Xinerama removal and blank-screen reports on certain Wayland compositors with HDR enabled.
- **CachyOS Forum** ([thread](https://discuss.cachyos.org/t/new-linux-driver-for-nvidia-display-driver-610-43-02/30335)): Discussion about distros being slow to ship 610 despite NVIDIA releasing it — 595 is still the default on many systems.

## Should You Install 610?

**Pros:** DRM color pipeline for better HDR on Wayland, Vulkan fixes (Doom, Starfield), FP16/DMABUF improvements for video pipeline
**Cons:** Feature branch (less tested than 595), blank screen risk on some compositors with HDR, Xinerama removed, GSP crash on RTX 5060 Ti not fixed

**Bottom line:** 610 does NOT fix the RTX 5060 Ti GSP crash or the Chrome banding. It has useful Wayland color improvements and Vulkan fixes but as a Feature branch may introduce new issues. Available in Manjaro extra repo as `nvidia-open-dkms 610.43.02-2` if you want to test.

## How to Check Your Current PCIe Link Status

Running at Gen 4 (downgraded) instead of Gen 5 is common on RTX 50-series and can be a diagnostic clue for stability issues:

```bash
# Check current negotiated speed and width
sudo lspci -vv -s $(lspci | grep NVIDIA | cut -d' ' -f1) | grep -A2 'LnkSta:'
# Speed 16GT/s = PCIe 4.0, 32GT/s = PCIe 5.0

# Check what the GPU and slot are capable of
sudo lspci -vv -s $(lspci | grep NVIDIA | cut -d' ' -f1) | grep -A3 'LnkCap:'
```

If `(downgraded)` appears next to the link status, PCIe training failed at the max capability and fell back. This does not measurably affect gaming performance but can be a signal of PCIe Gen 5 instability.

## Sources

- Phoronix: https://www.phoronix.com/news/NVIDIA-610.43.02-Linux-Driver
- GamingOnLinux: https://www.gamingonlinux.com/2026/05/nvidia-driver-610-43-02-arrives-for-linux-with-vulkan-upgrades-drm-colour-pipeline-api-support/
- UbuntuHandbook: https://ubuntuhandbook.org/index.php/2026/05/nvidia-610-43-02-released-with-hdr-output-support-for-linux/
- Tux Machines: https://news.tuxmachines.org/n/2026/05/26/NVIDIA_610_Linux_Graphics_Driver_Adds_Vulkan_and_Wayland_Improvements.shtml
- NVIDIA Dev Forum (610 feedback): https://forums.developer.nvidia.com/t/610-release-feedback-discussion/371356
- Reddit r/linux_gaming: https://www.reddit.com/r/linux_gaming/comments/1to7tnn/nvidia_driver_6104302_released_with_drm_color/
- CachyOS forum: https://discuss.cachyos.org/t/new-linux-driver-for-nvidia-display-driver-610-43-02/30335
- NVIDIA Unix Driver Archive: https://www.nvidia.com/en-us/drivers/unix/
