# EEVDF Scheduler — Kernel 7.0+ Transition Notes

## What Changed

Linux 6.6 replaced CFS with EEVDF (Earliest Eligible Virtual Deadline First). By kernel 7.0, CFS is fully removed — the old scheduler tunables no longer exist.

## Removed sysctl paths (return "No such file or directory" on 7.0+)

```
/proc/sys/kernel/sched_min_granularity_ns
/proc/sys/kernel/sched_wakeup_granularity_ns
/proc/sys/kernel/sched_latency_ns
/proc/sys/kernel/sched_cfs_bandwidth_slice_us
/proc/sys/kernel/sched_child_runs_first
/proc/sys/kernel/sched_migration_cost_ns
```

## Remaining EEVDF tunables

```
kernel.sched_autogroup_enabled      # 0 = disable terminal session grouping
kernel.sched_rt_runtime_us          # RT CPU bandwidth limit (-1 = unlimited)
kernel.sched_schedstats             # 0 = disable stats collection
kernel.sched_util_clamp_min         # Min utilization clamp (default 1024)
kernel.sched_util_clamp_min_rt_default
```

## EEVDF debugfs (root-required)

```
/sys/kernel/debug/sched/base_slice_ns    # Base time slice in nanoseconds
/sys/kernel/debug/sched/                 # Other EEVDF internals
/sys/kernel/sched_ext/state              # sched_ext active state
/sys/kernel/sched_ext/ops               # Active BPF scheduler name
```

## Key Behavioral Differences

1. **Auto-tuning**: EEVDF assigns virtual deadlines based on task "lag" — latency-sensitive tasks automatically get shorter slices. No manual tuning needed for most workloads.
2. **Decaying lag**: Sleeping tasks have their lag decay over virtual runtime, preventing "sleep to reset lag" exploits.
3. **`sched_setattr()`**: Tasks can request specific time slices via the new syscall. Used by PipeWire, gamemode, and RT applications.
4. **sched_ext**: Kernel 7.1+ supports sub-schedulers (scx_lavd, scx_bpfland, scx_rusty) loadable at runtime without kernel rebuild.

## Migration Checklist (from CFS to EEVDF)

- [ ] Remove any `sched_min_granularity_ns`, `sched_wakeup_granularity_ns`, `sched_latency_ns` from `/etc/sysctl.d/*.conf`
- [ ] Verify `sched_autogroup_enabled=0` (correct for desktop/gaming)
- [ ] Verify `sched_rt_runtime_us=-1` (required for PipeWire RT scheduling)
- [ ] Check `sched_schedstats=0` to disable statistics overhead
- [ ] Remove `sched_itmt_enabled=1` from GRUB if on Arrow Lake hybrid (ITMT is for single-architecture Xeon)

## Reference

Kernel docs: https://docs.kernel.org/7.0/scheduler/sched-eevdf.html
