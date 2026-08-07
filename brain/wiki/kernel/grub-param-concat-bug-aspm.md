---
source_session: "20260709_193718_2e6307"
date: "2026-07-09"
category: kernel
related: [grub, aspm, pcie, latency]
---

# GRUB Parameter Concat Bug (ASPM Policy)

A space was missing between `pcie_aspm.policy=performance` and `sched_itmt_enabled=1` in `/etc/default/grub`, producing:
```
pcie_aspm.policy=performancesched_itmt_enabled=1
```

This made `pcie_aspm.policy` value `performancesched_itmt_enabled=1` (invalid → fallback to `[default]`). Actual current policy was `default` not `performance`, so PCIe link state transitions (L0s/L1) were cycling on every I/O — adding latency.

**Fix:** `sudo sed -i 's/pcie_aspm.policy=performancesched_itmt_enabled=1/pcie_aspm.policy=performance sched_itmt_enabled=1/' /etc/default/grub` then `sudo grub-mkconfig -o /boot/grub/grub.cfg` and reboot.

Always check GRUB params for missing spaces — a single missing separator silently breaks kernel boot parameters.

[[kernel-boot-params]] [[pcie-aspm-tuning]] [[latency-tuning]]
