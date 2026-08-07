---
source_session: "20260807_200428_ad9a51"
date: 2026-08-07
category: kernel
tags: [tuning, sysctl, tmpfiles, intel_pstate, dirty_ratio, config-audit, dead-config, tcp_low_latency, cpu0, latency-fix]
related: [intel-arrow-lake-kernel-cmdline-tuning, cpu-min-perf-pct-systemd-permanent, power-profiles-daemon-override-governor]
---

# Linux Tuning Config Audit — Dead & Conflicting Entries

Audit of `sethengine`'s CPU/tuning configs (kernel 7.1, Arrow Lake) found several **dead, conflicting, or misleading** entries that silently do nothing or fight each other:

## Dead entries (silent no-ops — safe to remove)

1. **`/etc/tmpfiles.d/10-gaming-cpu.conf` — DEAD.** tmpfiles.d runs before cpufreq sysfs nodes exist, so `echo performance > .../scaling_governor` and EPP writes are silent no-ops. The `energy_performance_preference` write also gets `-EBUSY` (HWP hardware locks it) and can never succeed. **Redundant** now that the resume hook sets governor (step 3) and hardware EPP is already `performance`.

2. **`net.ipv4.tcp_low_latency=1` — DEAD sysctl.** The knob was removed from the kernel years ago; the line in `99-performance.conf` is silently ignored. Remove it.

3. **`/etc/default/cpupower-service.conf` — EMPTY/DEAD.** All settings commented; `cpupower.service` runs but does nothing. Harmless, low priority (populate or disable).

## Conflicting entries

- **`vm.dirty_ratio` flip-flop:** resume hook step 4 sets `dirty_ratio=5` on every suspend→wake, but `99-vm-tune.conf` sets `dirty_ratio=10`. Value flips between 10 and 5 depending on last suspend. `99-vm-tune.conf` is canonical — **hook should NOT override it** (remove hook step 4 / dirty_ratio=5).

## Verified-good configs (no action)
sysctl.d live values (`swappiness=5`, `autogroup=0`, `timer_migration=0`, `bbr`, `sched_rt_runtime_us=-1`); `pin-irqs-dynamic` hook; kernel cmdline `preempt=full`, `skew_tick=1`, `intel_idle.max_cstate=1`, `cpufreq.default_governor=performance`; `tlb-thp.conf`/`workstation.conf` (THP=madvise, read_ahead=512).

## References
- [[intel-pstate-hwp-epp-locked-arrow-lake]]
- [[cpu-min-perf-pct-systemd-permanent]]