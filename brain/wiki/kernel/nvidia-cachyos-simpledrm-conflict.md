---
source_session: 20260725_203708_c96c74
date: 2026-07-25
category: kernel
tags: [nvidia, cachyos, simpledrm, drm, kwin, wayland, grub]
---

# CachyOS NVIDIA-DRM / simpledrm DRM Minor Conflict

**Problem:** On the CachyOS kernel (vs linux71), `simpledrm` initializes on DRM minor 0, pushing `nvidia-drm` to minor 1. When `kwin_wayland` opens `/dev/dri/card0`, it finds simpledrm instead of the NVIDIA device, causing a login loop/crash.

**Root cause:** The CachyOS kernel's `simpledrm` probes before `nvidia-drm` — unlike the linux71 kernel where simpledrm suppresses itself with "will not be probed".

**Fix:** Add `sysfb.disable=1` to the kernel cmdline to prevent simpledrm from initializing.

## Option A — Global (all kernels)

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="sysfb.disable=1 /' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

This also appears on non-CachyOS kernels (harmless — simpledrm already suppresses itself there).

## Option B — Per-kernel (CachyOS only)

Create a GRUB snippet that appends `sysfb.disable=1` only to CachyOS kernel entries.

## Notes

- `GRUB_CMDLINE_LINUX_CACHYOS` is a custom variable **not supported** by `grub-mkconfig` — it will be ignored.
- `sysfb.disable=1` only affects simple/firmware framebuffers; it doesn't touch the NVIDIA driver.
- No initramfs rebuild needed for kernel cmdline changes.

[[nvidia-595-grub-modprobe-env-kwin-config]]
[[nvidia-wayland-kwin-latency-policy]]
