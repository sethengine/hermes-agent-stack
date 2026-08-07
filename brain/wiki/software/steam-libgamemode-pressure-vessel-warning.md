---
source_session: 20260805_194109_36b076
date: 2026-08-05
category: software
tags: [steam, gamemode, pressure-vessel, steam-runtime, warning, benign]
related: [gamemode-cpu-pinning-input-lag]
---

# libgamemode.so "dlopen failed" Warning is Benign (Steam Runtime)

The `gamemodeauto: dlopen failed - libgamemode.so` warning from the Steam client is **not** a missing package — it's a Steam Runtime container limitation.

**Facts:**
- Host lib IS installed: `/usr/lib/libgamemode.so` + `/usr/lib32/libgamemode.so`, `ldconfig` sees it, packages `gamemode 1.8.2` + `lib32-gamemode 1.8.2` present, `gamemoded` service active
- The warning comes from the **Steam client process** (host-side Steam Runtime sandbox) whose `LD_LIBRARY_PATH` excludes host `/usr/lib`
- The **pressure-vessel container does not expose `libgamemode*`** to games (no override entry, x86_64 or i386) — Steam ships `libgamemodeauto.so` statically, so `dota.sh`/`gamemodeauto` looks for `libgamemode.so` inside the container and fails
- Pre-existing, permanent warning — identical on multiple days, unrelated to game crashes/audio

**Optional silence fix (expose host lib into runtime lib dir):**
```bash
RT_LIB=~/.local/share/Steam/ubuntu12_64/steam-runtime/lib/x86_64-linux-gnu
sudo ln -sf /usr/lib/libgamemode.so.0.0.0 "$RT_LIB/libgamemode.so.0"
```

Low-risk (just exposes an existing host lib), but cosmetic only — the warning is harmless.

[[Gamemode CPU pinning input lag]]
