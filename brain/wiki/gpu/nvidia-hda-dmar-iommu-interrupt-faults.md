---
source: 20260703_231509_6397bb
category: gpu
date: 2026-07-03
tags: [nvidia, hda, dmar, iommu, interrupt, fault, irte, nvidia-audio]
---

# NVIDIA HDA Audio DMAR IOMMU Interrupt Faults

The NVIDIA GB206 HDA audio function (PCI `02:00.1`) generates continuous DMAR IOMMU interrupt faults on Intel Arrow Lake (Z890 chipset). Fault log format:
```
[INTR-REMAP] Request device [02:00.1] fault index 0x788a
Present field in the IRTE entry is clear
```

**Impact:** Continuous kernel-level interrupt remapping faults add IRQ overhead (~2% GPU IRQ), creates 4 unused PipeWire sinks, competes for IRQ 226.

**Fix via kernel parameter** — disable NVIDIA HDA while keeping motherboard audio:
```
snd_hda_intel.enable=0,1
```
Card 0 (NVIDIA) disabled, card 1 (ALC1220) enabled. The PCI probe order determines which is 0 vs 1 — NVIDIA HDA probes first at `02:00.1`.

**Alternative** — PCI ID match (safer, order-independent):
Create `/etc/modprobe.d/nvidia-hda.conf`:
```
options snd_hda_intel enable=0,1
```

After applying, reboot and verify with `cat /proc/asound/cards`.

[[alc1220-sof-vs-hda-driver-conflict]]
[[hugepages-unused-waste]]
