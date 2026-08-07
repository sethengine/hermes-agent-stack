---
source: "session/20260630_223903_ba915f"
category: system
date: 2026-07-01
tags: [gigabyte, z890, vccsa, bios, voltage, arrow-lake]
---

# Gigabyte Z890 — Internal VCCSA vs CPU System Agent Voltage

On Gigabyte Z890 boards, there are **two separate VCCSA entries** in the Tweaker menu:

| BIOS Entry | Purpose | Recommendation |
|------------|---------|---------------|
| **CPU System Agent Voltage** | SVID target/request — tells CPU to ask VRM for a voltage | **Leave Auto** — changes don't stick |
| **Internal VCCSA** | Actual voltage override for the VCCSA rail | **Use this one** — directly programs the voltage regulator |

Per r/overclocking (nhc150) and SkatterBencher's Arrow Lake MemSS guide, `Internal VCCSA` is what you want for 4-DIMM stability. HWinfo may still show auto voltage even with a manual override — this is normal.

**Don't confuse with Memory Controller Voltage (VDD2)** — that's a separate third rail (analog PHY I/O, 1.10–1.20V).

[[gigabyte-z890-4-dimm-ddr5-stability]]
