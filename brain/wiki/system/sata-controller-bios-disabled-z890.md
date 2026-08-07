---
source_session: "20260606_201613_304efb"
category: system
tags: [sata, bios, ssd, nvme, storage, pci]
---

# SATA Controller Disabled in BIOS (Z890 Aero G)

On Gigabyte Z890 AERO G, the SATA controller can be **disabled in the UEFI/BIOS**, making it invisible to Linux — no PCI device shows up, no rescan works.

## Symptoms

- `lspci` shows no SATA controller
- `lsblk` shows only NVMe drives
- Hot-plugging a SATA SSD does nothing
- `dmesg | grep -i sata` returns nothing

## Diagnosis

Check the PCI bus for SATA class devices:

```bash
lspci | grep -i sata       # shows nothing if disabled
lspci -nn | grep 0106      # SATA controller class code
```

Check kernel AHCI module:

```bash
lsmod | grep ahci           # absent if no SATA hardware
```

## Fix

SATA controller must be **enabled in BIOS/UEFI** — cannot be fixed from within Linux. No kernel parameter, module load, or rescan re-enables a PCI device that is powered off at the firmware level.

- Reboot → enter UEFI setup → look for "Integrated Peripherals" or "SATA Configuration"
- On Gigabyte Z890 AERO G: **Advanced → SATA Configuration → SATA Controller → Enabled**
- Reboot — SATA drives appear in `lsblk` and `fdisk -l`

## Cannot hot-fix

Unlike a USB device, SATA on this board is wired through the PCH PCIe root complex. If the controller is disabled in firmware, no kernel operation (rescan, probe, pci=realloc) can bring it online. Requires physical reboot.

Related: [[gigabyte-z890-aero-g-bios]], [[gigabyte-z890-aero-g-prefdrive-bios-settings]]
