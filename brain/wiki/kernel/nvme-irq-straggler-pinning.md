---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [pin-irqs-dynamic-v4]
---

# NVMe IRQ Straggler Pinning Issue

Some NVMe MSI-X queue interrupts escape their assigned CPU affinity and land on GPU/USB-dedicated cores.

## The Problem

NVMe controllers manage their own MSI-X queue affinity and **override userspace affinity writes**. The kernel's NVMe driver reassigns queue interrupts to its preferred CPUs regardless of what `/proc/irq/N/smp_affinity_list` says.

## Observed Stragglers

```
IRQ 165 (nvme1q9)    → CPU9:  104,683  ← on GPU E-core (zone 8-11)
IRQ 166 (nvme1q10)   → CPU11:  83,306  ← on GPU E-core (zone 8-11)
IRQ 167 (nvme1q11)   → CPU13: 102,700  ← on USB E-core (zone 12-13)
IRQ 181 (nvme0q10)   → CPU9:       86  ← on GPU E-core
IRQ 183 (nvme0q12)   → CPU11:      78  ← on GPU E-core
IRQ 184 (nvme0q13)   → CPU12:      78  ← on USB E-core
```

## Mitigation

- Use `smp_affinity` (hex mask) instead of `smp_affinity_list` — more compatible with NVMe driver
- Run a periodic timer (every 100 min) that catches and re-pins stragglers
- Accept that NVMe may briefly escape between timer runs

## Impact Assessment

These straggler queues carry ~100K interrupts vs GPU IRQs with 1-2M+ on the same cores — <5% overhead. Practically negligible.

## Fix

The [[pin-irqs-dynamic-v4]] script includes a straggler catch timer that re-applies NVMe affinity every 100 minutes.
