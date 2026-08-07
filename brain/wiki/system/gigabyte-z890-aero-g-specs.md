---
source: "session/20260630_223630_8f64a2"
category: system
date: 2026-07-01
tags: [gigabyte, z890, aero-g, hardware, specs, arrow-lake]
---

# Gigabyte Z890 AERO G — System Specs

This machine's hardware configuration (confirmed 2026-06-30):

- **Motherboard:** Gigabyte Z890 AERO G (Rev. 1002), BIOS F17f (July 2025)
- **CPU:** Intel Core Ultra 7 265K (Arrow Lake-S), 20C/20T — 8 P-cores + 12 E-cores, no Hyper-Threading, max 5.5 GHz, stock TDP 250W
- **GPU:** NVIDIA GeForce RTX 5060 Ti, 16 GiB GDDR, driver 595.71.05
- **RAM:** 64 GB DDR5 (4×16 GB), all 4 DIMMs populated
- **Storage:** WD_BLACK SN850X 2 TB (NVMe PCIe 4.0), Kingston SA2000M8 1 TB (NVMe PCIe 3.0)
- **Audio:** Realtek ALC1220 with custom PipeWire + EasyEffects chain
- **Monitor:** HP X34 (3440×1440 @ 60 Hz, HDMI)

**⚠️ Known issues:**
- GPU runs at PCIe 4.0 x8 instead of x16 — suspected lane sharing with M.2 or PCIEX8 slot
- BIOS is 11 months behind (F21 available, June 2026)
- CPU governor set to `powersave`

[[gigabyte-z890-4-dimm-ddr5-stability]]
[[gigabyte-z890-bios-f21-update]]
[[rtx-5060-ti-pcie-x8-issue]]
