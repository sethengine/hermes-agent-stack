---
source: "session/20260630_223903_ba915f"
category: system
date: 2026-07-01
tags: [gigabyte, z890, ddr5, 4-dimm, memory, stability, arrow-lake]
---

# Z890 4-DIMM DDR5 Stability Guide

4 DIMMs on Z890/Arrow Lake is hard on the memory controller (IMC). Realistic max: DDR5-5200–5600 (not XMP speeds).

**Key voltages for stability:**
- **Internal VCCSA:** 1.15–1.25V — single most impactful adjustment. *Not* the same as "CPU System Agent Voltage" on Gigabyte Z890 (see separate entry).
- **VDD2 (Memory Controller Voltage):** 1.10–1.20V — analog PHY I/O rail
- **DRAM VDD/VDDQ:** XMP voltage (1.35V) up to 1.40V

**Gigabyte-specific tweaks:**
- Disable High Bandwidth Support — can cause instability with 4 DIMMs
- Disable Low Latency Support — tighten timings manually instead
- Enable Memory Context Restore — faster boot
- DDR5 Power Down Mode forced ON in F18–F20 (known Gigabyte BIOS limitation)
- Force Command Rate 2T if available

**Troubleshooting flow:** Flash latest BIOS → Load Optimized Defaults → PerfDrive "Optimization" → Enable XMP. If unstable: drop to DDR5-5600 manual freq, set VCCSA 1.20V, VDD2 1.15V, disable High Bandwidth/Low Latency, loosen timings.

**Memory training:** First boot after changes shows black screen for 3–5 minutes. Do NOT power off.

[[gigabyte-z890-vccsa-internal-vs-system-agent]]
[[gigabyte-z890-bios-f21-update]]
