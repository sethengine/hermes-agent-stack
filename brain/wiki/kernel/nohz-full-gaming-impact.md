---
source: "20260608_001440_375423"
date: 2026-06-13
category: kernel
---

# nohz_full and rcu_nocbs: Harmful for Gaming

## nohz_full=CPULIST

Stops kernel timer ticks on specified CPUs when only one task is running. Saves ~0.3% CPU overhead.

**Benefit:** Scientific computing, audio production (eliminates tick noise), benchmarks.
**Cost for gaming:** When the game thread sleeps (e.g., waiting for mouse input via `poll()`), the nohz_full CPU has no tick to wake it. Input interrupts arrive on E-cores (due to IRQ pinning), but the wake-up to the P-core is delayed by up to ~1 second → **input lag**.

## rcu_nocbs=CPULIST

Offloads RCU (Read-Copy-Update) cleanup callbacks from specified CPUs to kernel threads.

**Cost:** Adds cross-CPU cache bouncing — the P-core frees memory, the RCU callback runs on an E-core, invalidating P-core cache. Slower than running the callback on the same core.

## Recommendation for Gaming Desktops

Remove both from GRUB config:
```bash
sudo sed -i 's/ nohz_full=0-7 rcu_nocbs=0-7//' /etc/default/grub
sudo update-grub
# reboot
```

**Keep** IRQ pinning to E-cores — that actually helps by preventing device interrupts from landing on P-cores. The HPC flags (`nohz_full`, `rcu_nocbs`, `isolcpus`) are designed for dedicated workload nodes (render farms, CERN) and provide zero benefit for general workstation/gaming use.

Related: [[gamemode-cpu-pinning-input-lag]]
