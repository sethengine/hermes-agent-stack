# NVIDIA DMAR/IOMMU Crash Cascade (Separate from Xid Errors)

This is a **different crash mechanism** from GPU compute/driver Xid errors. DMAR fault storms originate from the GPU's HDMI audio function in the IOMMU layer, not from the GPU compute engine.

## When to Suspect DMAR Crash (Not Xid)

- System crashed but no Xid errors are found in journal
- Journal shows `DMAR: [INTR-REMAP]` faults instead of `NVRM: Xid` errors
- KDE configs reset on next boot (kwinrc corruption)
- PipeWire crashed or easyeffects coredump preceded the system crash

## Fault Signature

```
DMAR: [INTR-REMAP] Request device [02:00.1] fault index 0x...
  [fault reason 0x22] Present field in the IRTE entry is clear
```

Device `02:00.1` = NVIDIA GB206 High Definition Audio Controller (HDMI audio)

## Crash Cascade

```
DMAR faults (02:00.1 GPU audio) → GPU driver instability
  → nvidia_drm sync error → PipeWire crash → easyeffects coredump
    → KDE Qt6 apps crash → plasmashell SIGKILL
      → Journals corrupted, EFI dirty, kwinrc corrupted
```

## Fix

`pci=noats` in GRUB (disables PCIe ATS) is the primary fix. See the full investigation in: `linux-system-crash-investivation` skill, Phase 9.
