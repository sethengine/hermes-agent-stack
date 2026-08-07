---
session: 20260702_181110_04264a
date: 2026-07-02
category: kernel
tags: [scheduler, arrow-lake, scx, sched-ext, bpfland, eevdf, bore, rustland, lavd, intel, hybrid]
---

# Arrow Lake CPU Scheduler Comparison

Research from Reddit, Phoronix, and CachyOS community on the best scheduler for Intel Arrow Lake (Ultra 200 series) on Linux.

| Scheduler | Verdict | Notes |
|-----------|---------|-------|
| **scx_bpfland** ✅ | Best for Manjaro | C-based, no hwloc crashes, Gaming mode pins P-cores. Already in `scx-scheds`. |
| **EEVDF (stock)** | Safe default | Built into kernel since 6.6. Works well on Arrow Lake (no SMT, simpler hybrid topology). |
| **BORE (CachyOS)** | Strong custom pick | Best burst latency. Requires AUR `linux-cachyos` kernel. |
| **scx_lavd** | YMMV | Original gaming scheduler but causes stutters for some on Intel hybrid. |
| **scx_rustland** ❌ | Crashes on resume | Userspace Rust scheduler aborts after suspend due to hwloc topology inconsistency. |

## Recommendation for Manjaro

`scx_bpfland` in Gaming mode is the best balance of reliability and performance:

```bash
sudo mkdir -p /etc/scx_loader
sudo tee /etc/scx_loader/config.toml << 'EOF'
default_sched = "scx_bpfland"
default_mode = "Gaming"
EOF
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader SwitchScheduler su "scx_bpfland" 1
```

## References
- [[scx-rustland-resume-crash-arrow-lake]]
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[intel-pstate-epp-default]]
