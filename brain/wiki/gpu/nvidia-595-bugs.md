---
source: "20260603_234459_ebf65d"
date: 2026-06-13
category: gpu
---

# NVIDIA 595 Driver Bugs

## Bug #2: Wayland OpenGL Black Screen After Suspend/Resume

- **Driver:** 595.71.05
- **Symptoms:** After waking from suspend on Wayland, OpenGL applications (Blender, Krita, games) render black screen. Compositor continues but OpenGL contexts are broken.
- **Reportedly fixed by** 595.71.05, but community reports (Brisse) say the fix is incomplete.
- **Workaround:** Disable GSP firmware (`NVreg_EnableGpuFirmware=0`).

## Bug #11: GSP Crash on Suspend (Xid 120)

- **Driver:** 595.45.04 beta
- **Symptoms:** Xid 120 "GSP task exception: load access page fault" on suspend with `NVreg_UseKernelSuspendNotifiers=1`. System completely hangs.
- **Status:** Reported against beta. NVIDIA switched suspend mechanism from nvidia-suspend services to kernel suspend notifiers in this series.
- **NVIDIA Forum:** https://forums.developer.nvidia.com/t/system-crashes-on-suspend-with-595-45-04/363397
- **Workaround:** Same — `NVreg_EnableGpuFirmware=0`.

## Bug #1095 (Kernel 7.0 + Blackwell s2idle)

- nvidia-modeset: suspend crash (jump_label BUG) caused by missing objtool NOP conversion in DKMS build
- **Fix:** Drop `dkms-objtool-jl.sh` into driver source dir, append to `MAKE[0]` line in `dkms.conf`, rebuild DKMS.

Related: [[nvidia-595-suspend-resume-workaround]]
