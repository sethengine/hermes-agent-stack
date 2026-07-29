# Gaming Scheduler Tunables for Hybrid CPUs

## The Problem

Aggressive scheduler settings designed for "low latency" hurt gaming:

```
sched_min_granularity_ns=750000    # 0.75ms time slices → game preempted ~8x per 165Hz frame
sched_wakeup_granularity_ns=1000000 # 1ms — Chrome/Steam steal CPU from game after 1ms
sched_latency_ns=6000000           # 6ms cycle — too tight, over-preempts
```

## Recommended Gaming Values

```ini
# /etc/sysctl.d/99-performance.conf — scheduler section

# 3ms minimum time slice — game runs 4x longer before preemption
kernel.sched_min_granularity_ns=3000000

# 4ms wakeup granularity — background tasks can't easily steal from game
kernel.sched_wakeup_granularity_ns=4000000

# 12ms latency target — still responsive, doesn't over-preempt
kernel.sched_latency_ns=12000000

# Keep autogroup enabled (helps multi-threaded games)
kernel.sched_autogroup_enabled=1
```

## Gamemode Config

```ini
# ~/.config/gamemode.ini
[general]
desiredgov=performance
softrealtime=auto
renice=-5
inhibit_screensaver=1

[gpu]
apply_gpu_optimisations=accept-responsibility
nv_powermizer_level=1

[cpu]
# Optional: pin game to P-cores only (remove # to enable)
# pin_cores=yes
# cores=0-7
```

Usage in Steam: Right-click game → Properties → Launch Options:
```
gamemoderun %command%
```

For pinned P-core execution (no reboot needed, no isolcpus):
```
gamemoderun taskset -c 0-7 %command%
```

## Context Switch Investigation Cheatsheet

```bash
# Total CS rate
CTXT1=$(grep "^ctxt" /proc/stat | awk '{print $2}'); sleep 3; CTXT2=$(grep "^ctxt" /proc/stat | awk '{print $2}')
echo "CS/s: $(((CTXT2 - CTXT1) / 3))"

# Find top CS consumers (total > 5M)
for pid in $(ps -eo pid --no-headers | head -100); do
  v=$(grep "^voluntary" /proc/$pid/status 2>/dev/null | awk '{print $2}')
  nv=$(grep "^nonvoluntary" /proc/$pid/status 2>/dev/null | awk '{print $2}')
  [ -n "$v" ] && [ $((v + nv)) -gt 5000000 ] 2>/dev/null && echo "$(cat /proc/$pid/comm) PID $pid: V=$v NV=$nv"
done

# Check which core GPU IRQs are hitting
cat /proc/interrupts | grep nvidia | head -5

# Check IRQ affinity
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  echo "IRQ $irq: CPU $(cat /proc/irq/$irq/affinity_list)"
done
```

## Normal vs Abnormal CS Rates

| Context | CS/s | Interpretation |
|---|---|---|
| Idle desktop | 1K-5K | Normal |
| Browser + apps | 10K-50K | Normal |
| With Proton game | 50K-100K | Normal (wineserver adds CS) |
| 200K+ | Investigate | Likely GPU IRQs or aggressive scheduler |
