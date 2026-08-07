---
source_session: "20260613_075159_9fffb4"
date: 2026-06-13
category: kernel
tags: [intel_pstate, epp, cpupower, hwp, cpufreq, performance]
related: [cpupower-frequency-info, intel-pstate-hwp-mode]
---

# Intel P-State EPP "Default" Meaning

When `cpupower frequency-info` shows `energy_performance_preference: default`, it's not "unset" — it's an explicit sentinel meaning "use the firmware's default EPP value."

## Key Facts

- **intel_pstate** in HWP (active) mode means the CPU's on-die logic controls frequency directly
- EPP (Energy Performance Preference) is an HWP hint telling the CPU whether to prioritize performance or power savings
- **Valid EPP values:** `default`, `performance`, `balance_performance`, `balance_power`, `power`
- **`default`** maps to **0x80** on a 0–0xFF scale, which is `balance_performance` — the midpoint
- The `"performance"` cpufreq **governor** and EPP `"default"` coexist: the governor removes software-imposed frequency caps, while EPP provides the hardware bias hint

## Setting a More Aggressive EPP

```bash
cpupower set --energy-perf performance
```

This tells HWP "don't hold back voltage/frequency for power savings" — more aggressive than the default midpoint.

## Relevant Context

- [[cpupower-frequency-info]] shows the driver, governor, limits, boost state, and EPP
- In HWP mode, the hardware decides final frequency based on EPP hint plus workload
- Different by: `amd_pstate_epp` driver on AMD systems (same concept, different driver)
