---
source: 20260703_231509_6397bb
category: kernel
date: 2026-07-03
tags: [power-profiles-daemon, governor, cpufreq, pstate, performance]
---

# Power Profiles Daemon Overrides CPU Governor

`power-profiles-daemon.service` actively overrides the CPU scaling governor even when `intel_pstate=active` and the governor is set to `performance`. PPD switches the governor back to `balanced` or `power-saver` on system events (lid close, AC unplug, profile switch).

**Impact:** Undoes performance governor tuning. The user sets `performance` via tmpfiles.d or sysfs, but PPD silently reverts it.

**Fix — disable the service:**
```
sudo systemctl disable --now power-profiles-daemon.service
```

**Verification:** Check governor is stable after disable:
```
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

Unnecessary on desktop systems with `intel_pstate=active` — the hardware pstate driver handles frequency selection more efficiently than PPD.

[[intel-pstate-epp-default]]
[[intel-arrow-lake-kernel-cmdline-tuning]]
