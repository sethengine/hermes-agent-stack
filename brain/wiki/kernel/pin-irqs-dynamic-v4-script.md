---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [nvme-irq-straggler-pinning, cpupower-epp-performance, gsp-xwayland-crash-chain]
---

# pin-irqs-dynamic v4 Script

Complete IRQ pinning and CPU tuning script (version 4) installed as a systemd service.

## Component Summary

| Component | Detail | Persistence |
|-----------|--------|-------------|
| **GPU IRQs** | → E-cores 8-11 | NVIDIA driver respects affinity |
| **USB IRQs** (xHCI) | → E-cores 12-13 | xHCI driver respects affinity |
| **Background IRQs** (NVMe/WiFi/audio/eth) | → E-cores 14-19, best-effort hex mask | Stays fixed |
| **NVMe straggler catch** | Re-pins escaped NVMe queues every 100 min | Timer-based |
| **C-states** | POLL + C1 only on cores 8-13 (C2/C3 disabled) | Permanent until reset |
| **Governor** | `performance` on cores 8-13 | Permanent |
| **EPP** | `performance` via `cpupower -c <cpu> set --epp performance` | Permanent |

## Service File

`/usr/local/bin/pin-irqs-dynamic` with systemd service at `pin-irqs-dynamic.service`.

## How It Works

1. Writes kernel tunables (C-states, governor, EPP, IRQ affinity) — all revert on reboot
2. Has `2>/dev/null` fallbacks — safe, nothing breaks if a file doesn't exist
3. Periodically re-checks and re-pins straggler NVMe IRQs

## Verification

Check active IRQ distribution:
```bash
grep "nvidia\|xhci\|nvme" /proc/interrupts | awk '{printf "%s → ", $1; for(i=2;i<=NF;i++) if($i>0) printf "CPU%d:%d ", i-2, $i; print ""}'
```
