---
source: "20260704_213306_1e0f79"
date: "2026-07-04"
category: "kernel"
---

# pci=noats GRUB Fix for NVIDIA DMAR Faults

`pci=noats` disables PCIe Address Translation Services (ATS), which resolves DMAR interrupt remapping faults common with NVIDIA GPUs.

## Quick Install

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="pci=noats /' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg
sudo reboot
```

## Alternative Parameters

- `iommu.passthrough=1` — bypass IOMMU entirely for all devices
- Blacklist HDMI audio: `options snd-hda-intel enable=0,1` in `/etc/modprobe.d/alsa-fix.conf`

## Applies To

- NVIDIA RTX 5060 Ti (likely any Ampere+ GPU with HDMI audio)
- Manjaro Linux, any kernel with IOMMU enabled
- Symptoms: `DMAR: [INTR-REMAP]` fault storms from the GPU audio function (02:00.1)

## Related
- [[nvidia-dmar-fault-crash-cascade]]
