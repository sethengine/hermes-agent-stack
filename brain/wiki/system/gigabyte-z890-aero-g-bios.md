---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: system
tags: [gigabyte, z890, aero-g, bios, motherboard, firmware]
---

# Gigabyte Z890 AERO G BIOS Configuration

The workstation uses a Gigabyte Z890 AERO G motherboard with BIOS version F17f (dated 07/09/2025, American Megatrends UEFI firmware). This board supports Intel Core Ultra 200-series (Arrow Lake).

Known quirks:
- IOMMU enabled: `intel_iommu=on,igfx_off iommu=pt` — igfx_off disables the integrated GPU since a discrete NVIDIA card is used
- `iTCO_wdt` watchdog blacklisted via kernel cmdline: `modprobe.blacklist=iTCO_wdt` to prevent spurious watchdog resets
- PCIe native hotplug enabled: `pcie_ports=native`
- Multiple USB buses detected (4 buses) with ITE GIGABYTE device (048d:5711) presumably for onboard sensor/controller

## References
- [[manjaro-system-specs-arrow-lake]]
- [[intel-arrow-lake-kernel-cmdline-tuning]]
