---
source_session: 20260804_latency_background_game (uncatalogued final-day session)
date: 2026-08-04
category: software
tags: [mouse-latency, input-lag, background-game, dota2, kwin, compositor, priority-inversion, nice, scheduler, present-queue, zombie-window]
related: [gaming_resource_exhaustion_vs_kernel_latency, kwin_latency_compositor, kwin_safety_margin_restore, system_latency_audit_findings, usb_irq_priority_analysis, proton_ge_high_cpu_background]
---

# Background Game Causes System-Wide Mouse Lag (Priority + Compositor, NOT Memory/TLB)

Live-state **correction** to the older `gaming_resource_exhaustion_vs_kernel_latency` model. The old
file blamed resource exhaustion (247% CPU, VRAM, swap thrash, 800MiB free). On a **fresh low-load
state** (load 0.74/20 cores, 36GB RAM available, swap idle, GPU 6%) a backgrounded Dota 2 still
produced system-wide mouse lag. So the exhaustion model was *sufficient but not necessary* — there
are two load-independent mechanisms.

## Confirmed live evidence (sethengine, RTX 5060 Ti / KDE Wayland / kernel 7.x)
- dota2: **84 threads but a single thread pegged at 83% on core 7**, whole process `PRI 24 / NI -5 / TS` (boosted).
- kwin_wayland on core 4, 4.2%. VRR = Never (already fixed). RAM idle (MemFree stable, swap 2.9G idle, HugePages_Total 2048 Free 2048).

## Mechanism 1 — Priority inversion on the input path
Mouse travels USB IRQ → evdev → libinput → KWin input thread → compositor → present. A game at
**nice -5** (below normal) is scheduled **ahead of** KWin's input threads on contention. On different
cores its boosted priority still wakes constantly, widening scheduler/preemption jitter system-wide.
This is scheduler-level (milliseconds) — the cause of *ever-present* lag.

## Mechanism 2 — Compositor present queue / "zombie-window" present cliff
Even backgrounded, a non-occluded non-minimized game keeps submitting GPU presents to KWin. KWin
composites serially (scene walk → DRM commit once per refresh); one busy presenter shrinks the
scheduling window for **every other client** including the pointer. LDAT-measured ~3ms added to all
other windowed apps. This is the *system-wide* component. Exacerbated by boost: the game's presents
and the wakeups they cause out-prioritize input.

## Why memory/TLB are red herrings here
- 36GB available, swap idle → no reclaim; DRAM bandwidth nowhere near saturated (6% GPU, 2 channels).
- TLB is per-core (no cross-core pollution on modern x86); cost is nanoseconds; THP already compresses
  the 64KB-ish table footprint. THP `[always]` + THP 3.3GB + FileHugePages 3.6GB already absorbing it.
- The old file's RAM/swap/VRAM framing applied to a *different, exhausted* state — do not extrapolate it.

## Fixes (global, ranked)
1. **Stop the game preempting input**: raise its nice (or cgroup) so it sits *below* normal.
   GameMode (`gamemoderun %command%` in Steam launch opts) is the lazy path; explicit `nice 10`.
2. **Mute its presents when unfocused**: minimize it or move to another virtual desktop (LDAT-verified
   biggest win for other apps); or set a strict MangoHud `fps_limit` so a backgrounded instance doesn't
   present at max rate.
3. **Cut per-present cost globally**: `Kwinrc Compositing LatencyPolicy=LatencyLow` (NOT LowLatency,
   which is problematic) + `KWIN_DRM_OVERRIDE_SAFETY_MARGIN=-150` (feasible on NVIDIA 595+).

## tmpfiles.d note (sysfs persistence)
`/etc/tmpfiles.d/*.conf` runs via systemd-tmpfiles at boot; a `w` rule writes a value to a path each
boot — clean way to persist sysfs knobs (e.g. `w /sys/kernel/mm/.../max_ptes_none - - - - 511`).
Fields: Type Path Mode Owner Group Age Argument. Verify survived boot: read the sysfs path back.
Caveat: THP sysfs knob paths can move across kernel 7.x — tmpfiles logs a warning and skips if gone.

## Related
- [[gaming_resource_exhaustion_vs_kernel_latency]] — the superseded exhaustion-only model (correct for its exhausted state, not general)
- [[kwin_latency_compositor]] — compositor as bottleneck
- [[kwin_safety_margin_restore]] — DRM safety margin override
- [[system_latency_audit_findings]] — full kernel tweak inventory these don't touch
- [[usb_irq_priority_analysis]] — input IRQ path
- [[proton_ge_high_cpu_background]] — orphaned background game procs