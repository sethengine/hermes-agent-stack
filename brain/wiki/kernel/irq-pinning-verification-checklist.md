---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [pin-irqs-dynamic-v4-script, cpupower-epp-performance, gsp-xwayland-crash-chain]
---

# IRQ Pinning Verification Checklist

When verifying that pin-irqs-dynamic is actually active, check each tweak individually rather than assuming the service is working.

## Verification steps

| Tweak | How to verify | Expected |
|---|---|---|
| GPU IRQs → E-cores 8-11 | `grep nvidia /proc/interrupts` | Non-zero counts on CPUs 8-11 |
| USB IRQs → E-cores 12-13 | `grep xhci /proc/interrupts` | Non-zero counts on CPUs 12-13 |
| Background IRQs → E-cores 14-19 | `grep "nvme\|iwlwifi\|snd_hda\|enp" /proc/interrupts` | Affinity on CPUs 14-19 |
| C2/C3 disabled | `cpupower idle-info` | Only POLL + C1 on cores 8-13 |
| Governor = performance | `cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor` | "performance" on cores 8-13 |
| EPP = performance | `cat /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference` | May show "default" under governor=performance — expected lock behavior |

## Known quirk

EPP locked to "default" under `performance` governor is **not a problem** — the governor itself enforces max frequency. Do not try to force EPP change with temporary governor toggle.

[[pin-irqs-dynamic-v4-script]] [[cpupower-epp-performance]]
