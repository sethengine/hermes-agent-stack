---
source_session: 20260804_222206_b83689
date: 2026-08-04
category: kernel
tags: [tlb, thp, khugepaged, max_ptes_none, numa, hugepages, latency, memory]
related: [hugepages_unused_waste, hugepages_2m_pages, background_game_mouse_lag_priority_compositor, kernel_sysctl_config_conflicts_latency]
---

# TLB / THP / khugepaged Tuning (Live State on RTX 5060 Ti box)

On a 20-core gaming box with plenty of RAM, the TLB is already ~90% tuned.
Memory/TLB pressure is NOT the cause of background-game mouse lag (see
[[background_game_mouse_lag_priority_compositor]]).

## Live state (kernel 7.x)
- `THP = [always]` — the single biggest system-wide TLB lever. Every big anon allocation
  (game heaps, Qt, Chrome) auto-promotes to 2MB pages → shrinks TLB footprint ~4000× per entry.
- `defrag = defer` — collapse only when free, no stall.
- `khugepaged max_ptes_none = 409` — eagerness of merging 4k→2MB.
- `numa_balancing = 0` — GOOD: no migration → no TLB shootdown storms.
- HugePages: 2048×2M reserved (4GB), all free. AnonHugePages 3.3GB + FileHugePages 3.6GB live.
- `pgfault` 780M over 2 days on 20 cores = nothing.

## TLB background
Virtual→physical translation cached on-chip. Capacity tiny: 512 entries ×4KB = 2MB covered.
Beyond that → eviction → page-walk (RAM, ~100–500 cycles). TLB is **per-core** on modern
x86 (no cross-core pollution); cost is nanoseconds.

## Remaining knobs (ranked, modest gains)
1. **`khugepaged max_ptes_none` higher** (e.g. 511) — lets khugepaged merge regions not fully
   faulted, holding more of the working set as 2MB pages. RAM is plentiful so this is safe.
   Persist via systemd-tmpfiles `w` rule in `/etc/tmpfiles.d/` (THP sysfs knob paths can move
   across kernel 7.x — tmpfiles warns+skips if gone).

There is no "missing" TLB knob that feels like the VRR fix — the box is already well tuned.

## Related
- [[hugepages_unused_waste]] — unused persistent HugePages pool (different from THP)
- [[hugepages_2m_pages]]
- [[background_game_mouse_lag_priority_compositor]] — the real mouse-lag mechanisms
- [[kernel_sysctl_config_conflicts_latency]]