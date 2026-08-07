---
source: "session/20260630_223630_8f64a2"
category: system
date: 2026-07-01
tags: [gigabyte, z890, bios, q-flash-plus, f21, update]
---

# Gigabyte Z890 — Q-Flash Plus BIOS Update

BIOS F17f (July 2025) → F21 (June 2026, 12.47 MB). ~11 months of fixes including microcode updates, Secure Boot default, HUDIMM support, D5 Single Boost, CSME 19.0.5, RST VMD 20.2.0.5868.

**Q-Flash Plus procedure (no CPU/RAM needed):**
1. PC must be **OFF** (PSU switch ON — standby power needed)
2. Format USB drive to FAT32, rename BIOS file to `gigabyte.bin`
3. Insert into the **white USB port** marked "BIOS" on back I/O panel
4. Press the **Q-Flash Plus button** (labeled QF_PLUS on board)
5. LED blinks during flashing — wait until it stops
6. Boot normally

**Important:** Do NOT interrupt during flashing. F21 includes system security and stability improvements.

[[gigabyte-z890-aero-g-specs]]
