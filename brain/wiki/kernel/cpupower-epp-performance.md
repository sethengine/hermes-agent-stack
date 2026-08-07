---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [pin-irqs-dynamic-v4]
---

# Setting EPP via cpupower Instead of Direct sysfs

The `energy_performance_preference` sysfs file becomes read-only after the `performance` governor is set — writing to it directly fails silently.

## Problem

```bash
# This FAILS silently when governor is already "performance":
echo "performance" > /sys/devices/system/cpu/cpu$N/cpufreq/energy_performance_preference
```

The `performance` governor locks the EPP file. `cat` still shows `default` but writes are ignored.

## Solution

Use `cpupower` which handles the ordering correctly:

```bash
cpupower -c <cpu> set --epp performance
```

This must be called **before** the governor is set to `performance`, or use cpupower which bypasses the governor lock.

## Verification

```bash
for cpu in 8 9 10 11 12 13; do
  epp=$(cat /sys/devices/system/cpu/cpu$cpu/cpufreq/energy_performance_preference 2>/dev/null)
  echo "CPU $cpu: EPP=$epp"
done
```

Should show `EPP=performance` on all target cores.
