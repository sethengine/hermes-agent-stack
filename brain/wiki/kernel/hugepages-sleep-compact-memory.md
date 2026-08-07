---
source: 20260502_150358_5e17d2
category: kernel
date: 2026-07-06
tags: [hugepages, sleep, wake, memory-fragmentation, compact_memory, resume-hook]
---

# Hugepages After Sleep: Memory Fragmentation Fix with compact_memory

After S3 sleep/wake, pre-allocated HugePages can drop (e.g., 2048 → 512) because memory becomes fragmented during suspend/resume, preventing contiguous 2 MB block allocation.

## Fix

Add `compact_memory` before hugepage allocation in the resume hook:

```bash
# Defragment RAM so hugepages can find contiguous 2MB blocks
echo 1 > /proc/sys/vm/compact_memory

# Then allocate hugepages
echo 2048 > /proc/sys/vm/nr_hugepages
```

`compact_memory` triggers kernel memory compaction, moving pages to free contiguous blocks. This significantly improves hugepage allocation success after resume when memory is fragmented.

## References
- [[hugepages-for-latency]]
- [[hugepages-unused-waste]]
