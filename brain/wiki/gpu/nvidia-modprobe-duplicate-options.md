---
source_session: "20260709_193718_2e6307"
date: "2026-07-09"
category: gpu
related: [nvidia, modprobe, gsp-firmware, driver]
---

# NVIDIA Modprobe Duplicate Options

`/etc/modprobe.d/nvidia.conf` had two sets of `options nvidia` and `options nvidia_drm` blocks. The second set's `NVreg_EnableGpuFirmware=0` conflicted with the modern driver's GSP firmware — `nvidia-smi` showed GSP as active despite the override.

Second set wins for overlapping params, but both blocks are loaded. Should be consolidated into one block.

**Fix:** Deduplicate the options blocks in `/etc/modprobe.d/nvidia.conf`, keeping only one coherent set.

[[nvidia-driver-config]] [[gsp-firmware]] [[kernel-module-params]]
