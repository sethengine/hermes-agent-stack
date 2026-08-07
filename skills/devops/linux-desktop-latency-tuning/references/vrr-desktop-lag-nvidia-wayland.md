# VRR / AdaptiveSync on the Desktop = Perceived Lag (NVIDIA Wayland)

Real case, 2026-08-01 on sethengine's system (Manjaro, KDE 6 Wayland, RTX 5060 Ti
driver 610, HP X34 3440x1440@165, kernel 7.1.4). The system was already heavily
tuned (preempt=full, C1 lock, 1ms USB polling, perf governor, IRQ pinning) but the
user reported "huge input lag / sluggish" — including in Dota 2 even pinned to P-cores.

## Root cause

`kwinrc` had `VrrPolicy=2` (KDE "Automatic" = per-window adaptive sync, desktop
included) and `AdaptiveSync=true`. With NVIDIA Wayland, the monitor refresh then
hunted continuously down to the VRR floor (~48 Hz on the HP X34). Desktop
compositing at a hunting refresh rate reads as lag/jank on every window, while
CPU/GPU looked idle (0-5% GPU, 97% idle cores).

Tellingly, the GPU sat at 637 MHz / P1 with the game at 322% CPU — the game itself
was fine; the DISPLAY path was the problem.

## Diagnostic signals

```bash
journalctl -b | grep 'Frame latency is negative'
# Chrome viz compositor: components/viz/service/display/display.cc:272
# "Frame latency is negative: -0.1 ms" — frames presented before deadline under VRR

kscreen-doctor -o | grep Vrr        # "Vrr: Automatic"  ← the bad state
```

Other systems checked healthy: no D-state processes, PSI ~0, no memory pressure,
swappiness/zram fixed, gateway ping 1.5 ms, USB IRQ rate normal.

## Fix

```bash
kwriteconfig6 --file kwinrc --group Compositing --key VrrPolicy 0    # Never
qdbus6 org.kde.KWin /Compositor reinitialize
```

or `3` = FullscreenOnly (VRR only in fullscreen games — keep if games want it).
User's words after `VrrPolicy=0`: "it's amazing". This was the single biggest
perceived-lag fix of the whole audit — bigger than swappiness/zram.

## VrrPolicy enum (KDE 6 kwinrc)

| Value | Meaning | kscreen-doctor shows |
|-------|---------|---------------------|
| 0 | Never (VRR off everywhere) | — |
| 1 | Always | — |
| 2 | Automatic (per-window; desktop included) | `Vrr: Automatic` |
| 3 | FullscreenOnly | — |

## Companion issue: Chrome negative frame latency persisted

Even after VRR-off, Chrome kept logging `Frame latency is negative` because the
running Chrome instance still used the OLD flags — flag files only apply to a
fresh process start. Also, `--use-angle=desktop` is NOT a valid value; the pair
`--use-gl=angle --use-angle=desktop` is ignored. Use `--use-gl=desktop` alone or
`--use-gl=angle --use-angle=vulkan`. Verify what the RUNNING process actually has:

```bash
tr '\0' ' ' < /proc/<chrome-gpu-pid>/cmdline | grep -oE '\-\-use-(gl|angle)=[a-z-]+'
```

## Residual load (not config bugs — usage)

After the config fixes, the remaining "sluggish" feel came from constant
background load: ~14 Chrome processes (~35% of a core), kwin 11%, easyeffects 5%,
Hermes 3.5%, Steam, omniroute/zed/opencode GPU apps. ~60% of one core always
busy. Fix = close unused apps/tabs, not config.
