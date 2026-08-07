---
source_session: "20260707_181617_f5bd6e"
date: 2026-07-07
category: kernel
tags: [cpu, min_perf_pct, intel_pstate, systemd, persistence, hwp, frequency]
related: [intel-pstate-epp-default, intel-arrow-lake-kernel-cmdline-tuning]
---

# CPU min_perf_pct — Systemd Permanent Tuning

Sysfs writes to `/sys/devices/system/cpu/intel_pstate/min_perf_pct` are runtime-only — lost on reboot. This covers making it permanent via systemd unit.

## The Setting

```bash
echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct
```

Default: **25** (CPU allowed to drop to 800 MHz floor). Setting to 70 keeps CPU in higher performance range, reducing wake-up latency.

## Permanent via Systemd Unit

```ini
# /etc/systemd/system/cpu-perf-tune.service
[Unit]
Description=Set CPU min_perf_pct for low-latency desktop
Before=display-manager.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable: `sudo systemctl enable --now cpu-perf-tune.service`

Fires before display manager so setting is active before KDE starts.

## Why Not energy_performance_preference?

On Arrow Lake with kernel 7.0 + `intel_pstate=active` (HWP mode), the EPP sysfs is **locked** — writes fail silently. Use `min_perf_pct` instead.

## ⚠️ Conflict: intel-min-perf.service clobbers the value (2026-07-31)

If `min_perf_pct` still reads 25 at runtime despite the tuning service, a competing unit is overwriting it **after** yours runs. Verified boot order:

```
17:54:41 cpu-perf-boot  → min_perf_pct=70   # intended value
17:54:41 cpu-perf-tune  → min_perf_pct=70, max=100, EPP=performance
17:54:49 intel-min-perf → min_perf_pct=25   # runs LAST, wins
```

Result: idle P-cores drop to 800 MHz → **first keypress/mouse-move after idle waits for a frequency ramp** (classic input lag on first input).

**Fix: disable the clobbering unit, re-apply the value now:**

```bash
sudo systemctl disable --now intel-min-perf.service
echo 70 | sudo tee /sys/devices/system/cpu/intel_pstate/min_perf_pct
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct        # verify: 70
```

Check for competing units with `systemctl list-units | grep -i perf` or grep `min_perf_pct` across `/etc/systemd/system/`.

## References
- [[intel-pstate-epp-default]]
- [[intel-pstate-hwp-epp-locked-arrow-lake]]
- [[system-latency-audit-findings]]
