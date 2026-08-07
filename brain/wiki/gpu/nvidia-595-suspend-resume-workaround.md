---
source: "20260603_234459_ebf65d"
date: 2026-06-13
category: gpu
---

# NVIDIA 595 Driver Suspend/Resume Workaround

NVIDIA 595 driver series has two key suspend/resume bugs that are both bypassed by disabling GSP firmware.

## The Fix Combo

```
options nvidia NVreg_EnableGpuFirmware=0
options nvidia NVreg_PreserveVideoMemoryAllocations=1
```

- `NVreg_EnableGpuFirmware=0` — disables GSP firmware, bypasses both the suspend crash (Xid 120) and the DPMS black-screen-on-wake
- `NVreg_PreserveVideoMemoryAllocations=1` — preserves framebuffer mappings across power state transitions

## Why It Works

595.45.04 beta introduced kernel suspend notifiers (`NVreg_UseKernelSuspendNotifiers=1`). These crash the GSP firmware on suspend (Xid 120 page fault). 595.71.05 fixed one bug but GSP still fails framebuffer restore on wake → black screen. Disabling GSP entirely sidesteps both.

## Alternative: Revert to 580.142

Some users (e.g., Brisse on GamingOnLinux) report 595.71.05 still broken and reverted to 580.142 — functionally the same workaround (older driver without the broken GSP suspend path).

## nvidia-sleep.sh Hack

For persistent cases: `echo "exit 0" | sudo tee /usr/bin/nvidia-sleep.sh` makes the sleep script a no-op (gets overwritten on driver update).

Related: [[nvidia-595-bugs]]
