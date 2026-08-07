---
source: "20260806_205721_d0f490"
category: software
date: 2026-08-06
tags: [gamemode, renice, nice, cap_sys_nice, dota2, priority]
---

# GameMode renice: CAP_SYS_NICE clamp, negation, and -high conflict

Why `renice` in gamemode.ini seems to do nothing, and why Dota's `-5` nice comes from Steam `-high`, not gamemode.

## `renice` key mechanics

- Must live under **`[general]`**, NOT `[realtime]` (gamemoded ignores it elsewhere)
- **GameMode NEGATES the value**: `renice=5` → applies nice `-5`. Writing `renice=-5` would give `+5` (worse priority). Use a *positive* number.
- A normal user cannot set a *negative* nice — the kernel clamps to `0` or returns `EACCES`. To apply a negative nice, `gamemoded` needs the capability:

```bash
sudo setcap cap_sys_nice+ep /usr/bin/gamemoded
# then restart gamemoded (kill + it auto-respawns via dbus/steam)
```

The smoking gun is `CapEff: 0000000000000000` on gamemoded — without it, no renice value in the ini will ever apply.
- `/etc/gamemode.ini` was dead weight until the cap was granted.

## The Dota -5 came from `-high`

Dota's cmdline `.../dota2 -vulkan -high -novid` — the **`-high`** Steam launch option is what sets nice `-5`, independent of GameMode.

## Fix

1. `sudo setcap cap_sys_nice+ep /usr/bin/gamemoded` + restart gamemoded
2. Remove `-high` from Steam launch options so it doesn't fight gamemode
3. `~/.config/gamemode.ini`: `[general] renice=5` (→ nice -5; use 10 for -10)

## References
- [[gamemode_cpu_pinning_input_lag_document]]
- [[software_dota2_vulkan_launch_optimization]]
- [[steam_libgamemode_pressure_vessel_warning]]