---
source: 20260502_150358_5e17d2
category: kernel
date: 2026-07-06
tags: [hugepages, sleep, wake, memory-fragmentation, drop-caches, aggressive]
---

# Hugepages Aggressive Recovery After S3 Sleep

Basic `compact_memory` alone may not recover 2048 hugepages after sleep when memory is heavily fragmented. Use aggressive strategy.

## Aggressive Strategy: Drop Caches + Multi-Round Compaction

```bash
# Post-sleep in resume hook:
echo 3 > /proc/sys/vm/drop_caches        # Wipe clean caches
echo 1 > /proc/sys/vm/compact_memory     # Round 1
sleep 3
echo 1 > /proc/sys/vm/compact_memory     # Round 2
sleep 2
echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
```

## Pre-Sleep Allocation

Allocate hugepages in the pre-suspend hook so S3 preserves them in RAM:
```bash
echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
```

## Falls Short? More Options

1. **Systemd timer** — retry allocation every 30s after wake
2. **swapoff/swapon** — frees RAM for hugepages before sleep
3. **s2idle instead of S3** — shallower sleep preserves allocations
4. **GRUB hugepages=2048** — kernel-allocated at boot

## References
- [[hugepages-sleep-compact-memory]]
- [[hugepages-unused-waste]]
