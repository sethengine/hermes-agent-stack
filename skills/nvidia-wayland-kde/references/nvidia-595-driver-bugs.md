# NVIDIA R595 Linux Driver — Bug Reference (March–June 2026)

## Driver Timeline

| Version | Date | Type | Notes |
|---------|------|------|-------|
| 595.45.04 | Mar 5 | Beta | First R595 public build |
| 595.58.03 | Mar 24 | Stable | First production R595 — major feature + fix release |
| 595.71.05 | Apr 28 | Stable | Single bug-fix release (Wayland OpenGL suspend/resume) |

Current latest on NVIDIA's Unix Driver Archive: Production branch **570.169**, New Feature **575.64.03**, Beta **575.51.02**. The 595 branch has been superseded.

## Known Bugs and Crashes

### Bug #1 — Xid 31 MMU Fault → Xid 154 System Freeze (Chromium/NVDEC)

**Issue:** [GitHub NVIDIA/open-gpu-kernel-modules #1134](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1134)

**Trigger:** Chromium-based browser (Chrome, Brave) GPU workload on Wayland. BAR1 VA space gets exhausted by `dmaAllocMapping_GM107`, then the driver makes an arithmetic mistake computing the fallback range, requesting memory past BAR1's end.

**Crash cascade:**
```
resource sanity check (BAR1 range exceeded) → Xid 31 (MMU fault CE2)
→ Xid 154 (Node Reboot Required) → Xid 175 (GSP RPC timeout, 75s)
→ Display freeze → system hard-locks
```

**Recovery:** Hardware power button hold required. `nvidia-smi` hangs, `systemctl reboot` hangs at nvidia_drm teardown.

**Fix:** None from NVIDIA yet. Workaround: `chrome --disable-accelerated-video-decode` or revert to kernel 6.19.x + driver 595.58.03.

### Bug #2 — Wayland OpenGL Black Screen After Suspend/Resume

**Fix:** 595.71.05 — restores framebuffer mappings during resume.
**Note:** Some users report fix is incomplete; reverting to 580.142 may be necessary.

### Bug #3 — Kernel Panic with CONFIG_RANDSTRUCT_FULL

**Fix:** 595.58.03 — fixed crash on hardened kernels.

### Bug #4 — Kernel Crash on DisplayPort MST / Thunderbolt Dock Disconnect

**Fix:** 595.58.03 — null pointer dereference in nvidia-modeset fixed.

### Bug #5 — X11 Compositor Flicker Regression

**Fix:** 595.58.03 — flicker in picom/Xfwm (regression from 580.119) fixed.

### Bug #6 — KWin Wayland Display Wake Failure

**Fix:** 595.58.03 — displays fail to wake from sleep in certain MST scenarios.

### Bug #7 — Blackwell cuTensorMapEncodeTiled() Memory Error

**Fix:** 595.58.03 — illegal memory access with tensors <128KB on Blackwell (RTX 5090, RTX PRO 6000).

### Bug #8 — Xid 109 CTX SWITCH TIMEOUT (Crimson Desert / The Last of Us)

**Workaround:** `VKD3D_CONFIG=no_upload_hvv` or use vkd3d-proton with non-merged VK_EXT_descriptor_heap.

### Bug #9 — Elden Ring World-Load Freeze on RTX 5090 + 595.58.03

**Status:** Unresolved. Multiple workarounds tried (taskset, shader cache clear, VRR disable) — none worked.

### Bug #10 — Linux 6.19 Kernel Module Build Failure

**Fix:** 595.58.03 — DKMS build fix for kernel 6.19 API changes.

### Bug #11 — GSP Crash on Suspend (Xid 120) — 595.45.04 Beta

**Issue:** Memory barrier assertion failure during suspend with NVreg_UseKernelSuspendNotifiers=1.

## Suspend/Resume Workarounds (Kernel 7.0 + NVIDIA)

**DKMS objtool workaround** — [NVIDIA/open-gpu-kernel-modules #1095](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1095):
Drop `dkms-objtool-jl.sh` into the driver source dir and append it to the `MAKE[0]` line in `dkms.conf`. This passes an extra objtool pass that the nvidia-open DKMS build skips on kernel 7.0. **Gets overwritten on driver upgrade.** NVIDIA bug 6120895.

**nvidia-sleep.sh exit-0 hack** (last resort):
```bash
echo "exit 0" | sudo tee /usr/bin/nvidia-sleep.sh
```

## Version Recommendation Table

| If you have... | Use... | Why |
|---|---|---|
| Blackwell GPU (RTX 50-series) | 595.58.03+ | Fixes cuTensorMap memory bug, enables CUDA P0 state |
| Wayland + suspend/resume issues | 595.71.05 | Fixes OpenGL black screen after resume |
| Linux kernel 6.19+ | 595.58.03+ | Kernel 6.19 build fix |
| X11 compositor flicker | 595.58.03+ | Fixes picom/Xfwm regression |
| RTX 30-series + Chromium crashes | 580.142 or 590 | #1134 BAR1 exhaustion still open on 595 |
| Hardened kernel (RANDSTRUCT) | 595.58.03+ | Kernel panic fix |

## Sources

- GitHub NVIDIA/open-gpu-kernel-modules #1134: https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1134
- GitHub NVIDIA/open-gpu-kernel-modules #1095 (DKMS objtool fix): https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1095
- Linuxiac — 595.58 release notes: https://linuxiac.com/nvidia-595-58-linux-driver-released-with-multiple-kernel-crash-fixes/
- Phoronix — 595.58.03 stable R595: https://www.phoronix.com/news/NVIDIA-595.58.03-Linux
- GamingOnLinux — 595.71.05: https://www.gamingonlinux.com/2026/04/nvidia-595-71-05-stable-driver-released-for-linux
- NVIDIA Developer Forum — 595 feedback: https://forums.developer.nvidia.com/t/595-release-feedback-discussion/362561
- NVIDIA Driver r595 Installation Guide: https://docs.nvidia.com/datacenter/tesla/pdf/Driver_Installation_Guide.pdf
- Framework Community — Kernel 7.0 suspend hang: https://community.frame.work/t/fw16-with-nvidia-suspend-resume-seems-broken-on-ubuntu-26-04/82026
- Abhik Sarkar — Xid 31 MMU faults deep dive: https://www.abhik.ai/articles/gpu-xid31-mmu-faults
