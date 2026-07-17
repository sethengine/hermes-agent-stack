# Linux Kernel 7.0+ Epochal Changes for Latency Tuning

## Releases
| Kernel | Release Date | Key Latency Features |
|--------|-------------|---------------------|
| 7.0 | 2026-04-12 | Preemption model restriction, hybrid CPU scheduler rewrite, NTSYNC stabilized, dmem cgroup, XFS self-healing |
| 7.1 | 2026-06-14 | Intel FRED by default, sched_ext sub-scheduler support, BTF io_uring, 140K+ lines legacy code removal |
| 7.2-rc2 | 2026-07-05 (testing) | Stable target late August 2026 |
| 7.3 | Late 2026 (pipeline) | "Flatten the pick" patches, DRM scheduler latency improvements, i915+RT integration |

## Preemption Model Restriction (7.0)
- Voluntary and basic preemption modes DROPPED
- Valid modes now: `preempt=full` and `preempt=lazy`
- `preempt=full` remains correct for desktop latency
- Lazy = full preemption except RCU read-side critical sections
- Patch by Peter Zijlstra (Intel), hit sched/core branch

## Intel FRED (7.1)
- Flexible Return and Event Delivery — architectural rework of CPU exception/interrupt delivery at hardware level
- Enabled by default on Panther Lake+ platforms
- Reduces overhead in interrupt-heavy workloads (networking, real-time audio, high-rate I/O)
- Older Intel hardware: feature ignored, no regression
- Source: Phoronix, LinuxTeck, Kernel Newbies

## Hybrid CPU Scheduler Rewrite (7.0)
- Completely redesigned task scheduler targeting Intel hybrid architectures
- Latency-sensitive tasks (audio, UI, game engines) dynamically pinned to P-cores
- Background tasks (package managers, indexers) routed to E-cores
- 8-12% battery life improvements on Nova Lake testbeds (Phoronix)
- Based on task history + real-time runqueue depth monitoring

## sched_ext Sub-Scheduler Support (7.1)
- Multiple scheduler policies can coexist in same kernel build
- Runtime-loadable BPF schedulers: scx_lavd, scx_bpfland, scx_rusty
- BORE (CachyOS default) continues to work on 7.x
- No kernel rebuild needed to switch schedulers

## NTSYNC Driver (stabilized 7.0)
- Windows NT synchronization primitives in-kernel for Wine/Proton
- Previously emulated in userspace — significant CPU overhead in multi-threaded games
- 15-25% FPS improvement in Cyberpunk 2077, Microsoft Flight Simulator (GamingOnLinux)
- Verify: `lsmod | grep ntsync`

## DRM Scheduler Patches
- Lower GPU job submission latency when system loaded with many runnable CPU processes
- Phoronix, July 2026 — in pipeline for 7.2/7.3

## "Flatten the Pick" Patches (queued for 7.3)
- Improved cgroup scheduling for gaming on older hardware
- Phoronix, July 2026

## PREEMPT_RT Status (2026)
- Most of PREEMPT_RT merged mainline as of kernel 6.x
- Remaining out-of-tree: i915 DRM graphics driver adjustments
- Work ongoing to make Intel graphics code RT-compatible (Phoronix, July 2026)
- IRQ thread priorities: timer IRQ ≥80, network IRQ ≥50, storage IRQ ≥30
- Memory locking: `mlockall(MCL_CURRENT | MCL_FUTURE)`
- CPU isolation: `isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3`

## Deprecated/Removed
- `intel_idle/max_cstate` sysfs path: does NOT exist on 7.0+. Use GRUB `processor.max_cstate=1`
- Intel i486 sub-architecture: removed in 7.1 (140K+ lines)
- UDP Lite: removed in 7.1
- IPv6 module mode (`CONFIG_IPV6=m`): must be `=y` or `=n` on 7.1+
- AF_ALG: deprecated in 7.2, being further restrained in 7.3

## References
- Phoronix: https://www.phoronix.com/news/Linux-Restrict-Preempt-Models
- FOSS Linux 7.0: https://www.fosslinux.com/154929/linux-kernel-7-0-new-features.htm
- LinuxTeck 7.1: https://www.linuxteck.com/linux-kernel-7-1-release/
- Kernel Newbies 7.1: https://kernelnewbies.org/Linux_7.1
- ProteanOS PREEMPT_RT: https://proteanos.com/doc/real-time-linux-preempt-rt-latency-2026/
