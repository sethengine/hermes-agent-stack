---
source: "session/20260630_223237_f87f6a"
category: kernel
date: 2026-07-01
tags: [kernel, it87, hwmon, sensors, voltage, z890, gigabyte]
---

# it87 Hardware Monitoring on Gigabyte Z890

Modern Gigabyte Z890 boards use an **iTE® I/O Controller Chip** for hardware monitoring (voltages, fans, temps). The Linux `gigabyte-wmi` driver only exposes 6 temperatures — no voltages.

**Solution:** Load the `it87` kernel driver:
```bash
sudo modprobe it87 ignore_resource_conflict=1
```
Then `sensors` reports all voltages (Vcore, +12V, +5V, +3.3V, DRAM VDD).

**Normal voltage ranges (Z890 AERO G + Ultra 7 265K):**
- CPU Vcore: 0.65–0.95V idle, 1.15–1.35V load
- VCCSA: 0.85–1.10V auto (0.95V typical)
- VCCIO: 0.85–1.05V auto (0.92V typical)
- DRAM VDD: 1.10V JEDEC (XMP: 1.25–1.45V)
- DRAM VDDQ: matches VDD
- DRAM VPP: 1.80V (always)
- +12V: 11.4–12.6V, +5V: 4.75–5.25V, +3.3V: 3.14–3.47V

**WMI note:** The `DEADBEEF-1000` WMI GUID on Gigabyte Z890 boards is flagged "expensive" and likely holds full sensor data that `gigabyte-wmi` doesn't expose yet. The iTE chip is at SMBus 0x44.

[[gigabyte-z890-aero-g-specs]]
[[gigabyte-z890-bios-f21-update]]
