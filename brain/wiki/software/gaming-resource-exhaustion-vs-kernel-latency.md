---
source_session: 20260502_150358_5e17d2
date: 2026-07-17
category: software
tags: [dota2, input-lag, latency, swap, vram, gaming, diagnostics, kernel]
related: [system-latency-audit-findings, gamemode-cpu-pinning-input-lag, proton-ge-high-cpu-background, dota2-wayland-cursor-trap-fix]
---

# Gaming Resource Exhaustion Overrides Kernel Latency Tweaks

Well-tuned kernel latency settings (`preempt=full`, `threadirqs`, `performance` governor, `usbhid` polling=1, hugepages, IRQ pinning, nohz_full, cyclictest <100µs) are **necessary but not sufficient** when system resources are exhausted by a running game.

## Case: Dota 2 Left Running in Background

A system with all kernel tweaks verified active still exhibited severe inconsistent input lag. Root cause:

| Resource | Measurement | Impact |
|----------|-------------|--------|
| CPU | 247% (Dota 2) | Game fighting compositor for GPU time |
| VRAM | 3.2 GiB (Dota 2) + 1.1 GiB (Chrome) | GPU memory pressure → unpredictable stutter |
| RAM | 7.1 GiB (Dota 2) | System-wide memory starvation |
| Swap | 2.7 GiB used | Every page fault causes a latency spike |
| Free RAM | ~800 MiB | No headroom for background tasks |

## Diagnostic Principle

When investigating input lag with all kernel tweaks apparently correct, always check:

```bash
# Is a game consuming resources in the background?
top -bn1 | head -20
nvidia-smi
free -h
swapon --show
```

A single game process at 247% CPU and 3.2 GiB VRAM **will defeat any kernel priority stack** — no amount of preempt=full, threadirqs, or IRQ pinning can compensate for swap thrashing and GPU contention.

## Key Facts

- `__GL_SYNC_TO_VBLANK=0` only affects OpenGL apps — **not Vulkan games** like Dota 2
- GPU contention (game + compositor + Chrome + Hermes Desktop) causes *inconsistent* stutter, not uniform lag
- 2.7 GiB swap + 800 MiB free RAM means every minor page fault triggers a block — the latency ceiling is determined by swap I/O, not kernel preemption
- Closing the game frees 247% CPU, 3.2 GiB VRAM, and 7 GiB RAM instantly
- Use `gamemoderun %command%` in Steam launch options for automatic GameMode optimization

## Related

- [[system-latency-audit-findings]] — comprehensive audit of all kernel tweaks
- [[gamemode-cpu-pinning-input-lag]] — specific nohz_full + gamemode pin interaction
- [[proton-ge-high-cpu-background]] — orphaned Proton processes after game exit
