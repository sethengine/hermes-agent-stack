---
category: software
source_session: 20260702_180259_6c64a4
date: 2026-07-02
tags: [nvidia, rtx-5060-ti, gb206, driver-595, manjaro]
---

# GeForce RTX 5060 Ti (GB206) — Early Notes

## Hardware

- **GPU:** NVIDIA GB206 [GeForce RTX 5060 Ti] (rev a1)
- **Subsystem:** ASUSTeK Computer Inc. (ID 1043:8A43)
- **Driver:** nvidia 595.71.05 (proprietary)

## Notable Observations

### License string change
Driver 595.71.05 reports `modinfo -F license nvidia` as `"Dual MIT/GPL"` instead of the traditional `"NVIDIA"`. This affects [[nvidia-driver-595-exec-condition-fix]] for systemd suspend/resume services.

### Kernel modules loaded alongside NVIDIA
The `i915` (Intel integrated GPU) module is also loaded, driving Intel Corporation Device 7f2f (display engine) on this platform.

### Config
NVIDIA module params on this system:
- `NVreg_EnableMSI=1`
- `NVreg_PreserveVideoMemoryAllocations=1`
- `NVreg_TemporaryFilePath=/var/tmp`
- `NVreg_DynamicPowerManagement=0x02`
- `NVreg_UsePageAttributeTable=1`
- `NVreg_EnableResizableBar=1`
- `NVreg_EnableGpuFirmware=0`
- `NVreg_RegistryDwords` with power/perf tuning

## Related

- [[nvidia-driver-595-exec-condition-fix]]
- [[manjaro-nvidia-suspend-troubleshooting]]
