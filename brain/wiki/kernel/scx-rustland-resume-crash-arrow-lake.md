---
session: 20260702_181110_04264a
date: 2026-07-02
category: kernel
tags: [scx-rustland, scheduler, crash, resume, suspend, hwloc, arrow-lake, topology]
---

# scx_rustland Crash After Resume on Arrow Lake

`scx_rustland` (userspace Rust sched-ext scheduler) crashes on Intel Arrow Lake after system resume from suspend. The abort occurs when hwloc detects a topology inconsistency in the cluster/L1d cache domain — Arrow Lake's cache layout differs from earlier generations.

## Symptoms
- System works fine until suspend/resume cycle
- After resume: `scx_rustland` ABRT crash
- Journal shows hwloc topology inconsistency error

## Fix
Switch to `scx_bpfland`, which is C-based and does not use hwloc for topology detection:

```bash
sudo mkdir -p /etc/scx_loader
sudo tee /etc/scx_loader/config.toml << 'EOF'
default_sched = "scx_bpfland"
default_mode = "Gaming"
EOF
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader SwitchScheduler su "scx_bpfland" 1
```

## bpfland Limitations

Unlike `scx_rustland`, `scx_bpfland` does **not** support performance/lowlatency/powersave modes — it's a single-purpose, always-balanced scheduler. No dynamic mode switching.

### Slice Sizes

| Mode | Slice | Use Case |
|------|-------|----------|
| Gaming | 20ms (default) | Games + desktop mix; stable scheduling slices for GPU command buffer submission |
| LowLatency | Smaller (more preemption) | Competitive/RT apps; increases context switch overhead |

For an aggressively-tuned system (preempt=full, C2/C3 off, performance governor), **Gaming** mode is the better choice — LowLatency adds scheduler overhead without noticeable latency improvement.

## References
- [[arrow-lake-scheduler-comparison]]
- [[nvidia-suspend-resume-black-screen]]
