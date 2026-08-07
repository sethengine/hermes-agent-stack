---
source: "20260608_001440_375423"
date: 2026-06-13
category: kernel
---

# Gamemode CPU Pinning Causes Input Lag

When `gamemode` CPU pinning is combined with `nohz_full` on the target cores, it causes ~1 second input lag.

## The Chain

1. `~/.config/gamemode.ini` has `[cpu] pin_cores=yes cores=0-7`
2. Game is pinned to P-cores 0-7
3. Those P-cores have `nohz_full=1-7` — no timer ticks when idle
4. Game thread calls `poll()` waiting for mouse input → goes to sleep
5. USB mouse interrupt arrives on E-core (where USB IRQ is pinned)
6. E-core signals wake-up to P-core
7. But P-core has **no tick** to process the wake-up promptly
8. Wake-up delayed until some other interrupt shakes the P-core → **~1 second input lag**

## Fix

Disable gamemode CPU pinning:
```bash
sed -i '/\[cpu\]/,/^\[/ {s/pin_cores=yes/pin_cores=no/}' ~/.config/gamemode.ini
```

Or remove the `[cpu]` section entirely. The game will run on all cores freely and nohz_full won't matter.
## GameMode Stop Command Overrides Scheduler

GameMode's `stop` command can silently **override** your scx scheduler choice. The config at `/etc/gamemode.ini` or `~/.config/gamemode.ini` may have:

```ini
[custom]
stop=scxctl switch -s rusty
```

Every time a game exits, GameMode runs that command, re-loading rusty **regardless** of what `scx_loader` config says. If you've switched to `scx_bpfland` but rusty keeps coming back, check both gamemode configs:

```bash
grep -r 'scxctl' /etc/gamemode.ini ~/.config/gamemode.ini
```

Fix by changing the stop command to bpfland (or removing the line):
```bash
sudo sed -i 's/switch -s rusty/switch -s bpfland/g' /etc/gamemode.ini
sudo sed -i 's/switch -s lavd/switch -s bpfland/g' /etc/gamemode.ini
sed -i 's/switch -s rusty/switch -s bpfland/g' ~/.config/gamemode.ini
```

## Related
- [[nohz-full-gaming-impact]]
- [[arrow-lake-scheduler-comparison]]
