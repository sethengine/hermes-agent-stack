---
source: "20260704_213306_1e0f79"
date: "2026-07-04"
category: "gpu"
---

# NVIDIA DMAR/IOMMU Fault Crash Cascade

System crash caused by DMAR interrupt remapping faults on the NVIDIA RTX 5060 Ti.

## Root Cause

NVIDIA GB206 High Definition Audio Controller (`02:00.1`) generated hundreds of:

```
DMAR: [INTR-REMAP] Request device [02:00.1] fault index 0x788d
  [fault reason 0x22] Present field in the IRTE entry is clear
```

The IOMMU interrupt remapping table entry for the GPU's audio function went invalid/missing.

## Failure Cascade

```
DMAR faults (02:00.1 GPU audio) → GPU driver instability
  → nvidia_drm sync FD error
    → PipeWire connection lost → easyeffects coredump
      → All KDE Qt6 apps crash: "no Qt platform plugin"
        → plasmashell killed with SIGKILL after systemd timeout
          → System journals corrupted, EFI dirty bit = unclean shutdown
```

## KDE Config Reset

kwinrc was being written at crash time. Result:
- `[Compositing] → Enabled=false` — animations/compositing off
- `AnimationSpeed=0` zeroed out
- `kconf_update` reset corrupted configs on next boot

## Additional Factors

- ACPI BIOS error: `\\RPTS.DTFS` (suspend/resume method) — motherboard firmware bug
- System: Manjaro Linux, NVIDIA 595.71.05 driver

## Quick Fix GRUB Command

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="pci=noats /' /etc/default/grub && sudo grub-mkconfig -o /boot/grub/grub.cfg
```

## KDE Restore Commands

```bash
kwriteconfig6 --file kwinrc --group Compositing --key Enabled true && \
kwriteconfig6 --file kwinrc --group Compositing --key AnimationSpeed 200 && \
kwriteconfig6 --file kwinrc --group Compositing --key Backend OpenGL && \
qdbus6 org.kde.KWin /Compositor resume && \
kwriteconfig6 --file kdeglobals --group KDE --key AnimationDurationFactor 1 && \
kwriteconfig6 --file kdeglobals --group KDE --key WidgetAnimationsEnabled true
```

## Related
- [[pci-noats-grub-fix]]
- [[dead-space-remake-hdr-gamescope]] (same GPU, same system)
- [[hermes-desktop-app-cpu-optimizations]] (GPU load context)
