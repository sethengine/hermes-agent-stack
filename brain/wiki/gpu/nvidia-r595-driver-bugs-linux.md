---
source_session: "20260612_215952_9a3bfb"
extracted_at: "2026-06-12T19:07:18Z"
category: "gpu"
tags: [nvidia, driver, r595, linux, wayland, xid]
---

# NVIDIA R595 Linux Driver Bugs

The NVIDIA R595 driver series on Linux has multiple known stability issues:

- **Xid 31 MMU fault → Xid 154 system freeze**: Triggered under Chromium-based browser GPU workload on [[nvidia-wayland-kwin-latency-policy|Wayland]]. `__nv_drm_gem_nvkms_map` requests a memory range exceeding PCI BAR1, leading to Xid 31 (MMU fault), followed by Xid 154 (Node Reboot Required). Reported on RTX 3090 with kernel 7.0.3 + nvidia-open 595.71.05. [GitHub issue #1134](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1134)
- **595.59 "unlaunched"**: Fan control and clock monitoring bugs — some fans stopped responding, custom fan curves ignored, only one fan sensor appeared in monitoring tools.
- **595.58.03 fixes**: Resolved kernel crashes, X11 compositor flicker, and Wayland display wake issues.
- **595.71.05 fix**: Fixed suspend/resume black screen for OpenGL apps on Wayland.

## Critical Note
The 595 branch is superseded by 570 (production) and 575 (new feature). The `nvidia-open` kernel module on R595 has persistent BAR1/mmap issues with high-memory GPU workloads.

## Related
- [[lact-gui-nvidia-segfault-fix|LACT GUI segfault]] — same driver version crashes LACT's GL context init
