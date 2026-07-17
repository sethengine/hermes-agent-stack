# SATA/PCI Bus Rescan for Hotplug Storage (No Reboot)

## Problem

A SATA SSD was physically connected to the motherboard but did not appear in `lsblk` or `/dev/sd*`. The user wanted to detect it without rebooting.

## Diagnostic Steps

### 1. Check if SATA controller exists on PCI bus

```bash
lspci | grep -iE 'sata|ahci|ata'
```

**If no results:** The SATA controller itself is **disabled in BIOS/UEFI**. It's not visible to the OS at all — no Linux-side fix can enable it. A PCI rescan (`/sys/bus/pci/rescan`) won't help because there's no PCI device to discover.

**If results appear:** Proceed to rescan.

### 2. Check for AHCI/libata drivers

```bash
ls /sys/class/scsi_host/       # SATA hosts (empty if no controller)
modinfo ahci                   # Check if AHCI driver is available (may be builtin)
ls /lib/modules/$(uname -r)/kernel/drivers/ata/  # Available ATA modules
```

AHCI and libata are often built into the kernel (shown as `(builtin)` in modinfo) on modern distros.

### 3. Attempt PCI bus rescan

```bash
# Write 1 to the PCI bus rescan file (requires root)
echo 1 | sudo tee /sys/bus/pci/rescan
```

Then check:
```bash
lsblk -o NAME,SIZE,MODEL,TRAN
```

### 4. If the controller was enabled at boot but not scanning an already-connected drive

Rescan SCSI/SATA hosts (only applicable after step 1 succeeds):

```bash
echo "- - -" | sudo tee /sys/class/scsi_host/host*/scan
```

## Fixed by BIOS change

On a **Gigabyte Z890 AERO G** motherboard with **Intel Z890 chipset**, the SATA controller was **disabled in BIOS** by default. Required action:
1. Reboot, enter BIOS (Del/F2)
2. Navigate to: *Peripherals* → *SATA Configuration* → *SATA Controller* → **Enabled**
3. Set *SATA Mode* to **AHCI**
4. Save & exit

After the reboot, the SATA controller appeared on the PCI bus and the drive was detected.

## Known Chipset Quirks

| Chipset | SATA Status | Notes |
|---------|-------------|-------|
| Intel Z890 (800 Series PCH) | Often disabled by default | Z890 PCH is at `80:1f.0` — SATA controller PCI ID typically `8086:7f62` (AHCI) or `8086:7f63` (RAID) |
| Intel Z790/Z690 (700/600 Series) | Usually enabled | SATA controller at `00:17.0` if enabled |
| AMD AM5 (X670/B650) | Usually enabled | May use third-party SATA controllers at different PCI addresses |
