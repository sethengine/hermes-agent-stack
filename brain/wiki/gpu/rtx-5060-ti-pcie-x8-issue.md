---
source: "session/20260630_223630_8f64a2"
category: gpu
date: 2026-07-01
tags: [nvidia, rtx-5060-ti, pcie, lane-sharing, x8, performance]
---

# RTX 5060 Ti — PCIe 4.0 x8 Lane Issue

GPU confirmed running at PCIe 4.0 x8 instead of expected x16.

**Possible causes:**
- GPU not in top PCIEX16 slot
- **PCIEX8 slot populated** — shares bandwidth with PCIEX16 (both drop to x8)
- M.2 NVMe configured to share lanes with PCIEX16
- BIOS PCIe speed negotiation issue

**Check and fix steps:**
1. Verify GPU is in top slot (PCIEX16, closest to CPU)
2. Check if anything occupies the PCIEX8 secondary slot
3. Reseat GPU and check `lspci -vvvs 02:00.0` after reboot
4. Enforce PCIe Gen4/Gen5 speed lock in BIOS (Settings → PCIe Subsystem)
5. Check M2A_CPU lane configuration in BIOS

**Impact:** Minimal for gaming at 3440×1440 (x8 Gen4 has equivalent bandwidth to x16 Gen3), but may bottleneck compute workloads.

[[gigabyte-z890-aero-g-specs]]
