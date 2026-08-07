---
source_session: "20260707_181617_f5bd6e"
date: 2026-07-07
category: kernel
tags: [kernel-7.0, preemption, full, lazy, voluntary, scheduling, latency, zijlstra]
related: [intel-arrow-lake-kernel-cmdline-tuning, linux-zen-kernel-latency]
---

# Linux 7.0 Preemption Model Restriction

Linux 7.0 (April 2026) restricts preemption models to **Full** and **Lazy** only, dropping voluntary and basic modes. Patch series by Intel's Peter Zijlstra targets the throughput/latency balance directly.

## What Changed

| Model | Kernel 6.x | Kernel 7.0 |
|-------|-----------|-----------|
| `preempt=none` | ✓ | ✗ dropped |
| `preempt=voluntary` | ✓ | ✗ dropped |
| `preempt=full` | ✓ | ✓ kept |
| `preempt=lazy` | ✗ | ✓ new |

## Why It Matters

- `preempt=voluntary` was the sensible default — good throughput, moderate latency. Now gone.
- `preempt=full` (PREEMPT_DYNAMIC in 6.x, now the default) gives lower scheduling latency at a small throughput cost
- `preempt=lazy` is a new middle ground: preempt on tick, not at every resched point — for throughput-sensitive workloads

## This System

Z890 265K runs **7.0.10-1-MANJARO** with `preempt=full` — already optimal for desktop/low-latency use. No change needed.

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[linux-zen-kernel-latency]]
