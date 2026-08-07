---
source: "session/20260630_223630_8f64a2"
category: system
date: 2026-07-01
tags: [gigabyte, z890, perfdrive, bios, stability, settings, arrow-lake]
---

# Gigabyte Z890 — PerfDrive & Stability BIOS Settings

**PerfDrive profile recommendation:** Spec Enhance (best stability/performance balance). Avoid Unleash for 4-DIMM setups.

**Critical stability settings:**
- **IA CEP (Current Excursion Protection):** Disable — prevents VRM throttling
- **Energy Efficient Turbo:** Disable — prevents voltage sag under load
- **GT CEP / SA CEP:** Leave Auto/Enabled

**Memory settings for stability:**
- XMP Profile 1 → if unstable drop frequency one notch
- High Bandwidth: Enable (free performance)
- Low Latency: Enable (free performance)
- Gear Down Mode: Enable (improves signal integrity at high speeds)
- Power Down Enable: Disable (reduces latency)

**Power limits:** PL1=PL2=250W (match CPU rated TDP)

**Undervolt recipe for 265K:**
1. IA CEP → Disabled
2. AC Loadline → 0.5 mOhm
3. DC Loadline → 1.0 mOhm
4. IA VR Voltage Limit → 1400 mV

[[gigabyte-z890-4-dimm-ddr5-stability]]
[[gigabyte-z890-aero-g-specs]]
