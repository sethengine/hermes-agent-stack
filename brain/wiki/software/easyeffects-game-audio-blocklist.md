---
source_session: 20260730_202842_a5d02b
date: 2026-07-30
category: software
tags: [easyeffects, dsp, audio, gaming, latency, pipewire, blocklist]
related: [pipewire-low-latency-config, pipewire-quantum-crackle-fix]
---

# EasyEffects Game Audio Blocklist

EasyEffects' full DSP chain (Bass Enhancer → EQ filters) adds 5-15ms audio latency per filter stage. When active on game audio, this compounds with PipeWire's force-quantum=256 (5.3ms base) to produce perceptible audio lag that contributes to the feeling of input lag in competitive games.

**Fix:** Block game audio from EasyEffects processing by creating `~/.config/easyeffects/blocklist.json`:

```json
["dota2", "steam", "steamwebhelper"]
```

Then restart: `systemctl --user restart easyeffects`

Via GUI: Hamburger menu → Preferences → Applications → Find the game in the audio stream list → Check "Block".

This bypasses the entire DSP chain for those applications, eliminating filter group delay for game audio while keeping it active for system notifications and media playback.
