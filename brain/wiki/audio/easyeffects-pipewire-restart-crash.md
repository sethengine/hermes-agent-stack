---
source: 20260606_201613_304efb
category: audio
date: 2026-07-14
tags: [easyeffects, pipewire, crash, race-condition, qt]
---

# EasyEffects Crash on PipeWire Restart (Race Condition)

EasyEffects 8.2.4 crashes with `SIGABRT` when **PipeWire is restarted underneath it** (e.g., `systemctl --user restart pipewire` while EasyEffects is running).

**Stack trace:** `PipeWire callback thread → EasyEffects DSP processing → Qt QDebug destructor → abort()`

**Root cause:** EasyEffects holds an open connection to PipeWire. When PipeWire exits, the connection becomes stale. EasyEffects' next processing cycle tries to read from the dead connection, triggering a `QDebug` destructor chain that hits `abort()`. This is a race condition in EasyEffects 8.2.4 — it has no reconnection logic for a disappearing PipeWire daemon.

**Symptoms:** 
- EasyEffects process exits with `SIGABRT` immediately after a PipeWire restart
- `easyeffects_sink` sink disappears from `wpctl status`
- Audio reverts to raw hardware output without EQ/effects

**Fix:** Kill the stale EasyEffects process and start a fresh one:
```bash
systemctl --user restart easyeffects
```

After restart, the plugin chain and `easyeffects_sink` are restored automatically from `~/.config/easyeffects/db/`.

**Prevention:** Always restart EasyEffects *after* PipeWire:
```bash
systemctl --user restart pipewire wireplumber
systemctl --user restart easyeffects
```

[[easyeffects-crash-missing-sink]]
[[easyeffects-corrupted-preset-crash-loop]]
[[pipewire-start-limit-hit-recovery]]
