---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-09"
category: audio
related: [pipewire, crackling, quantum, resampler]
---

# PipeWire Quantum Crackle Fix

Audio crackling was caused by `force-quantum = 0` in PipeWire config (quantum 1024 but free adaptation). During silent periods the quantum adapted down, and transitioning back up caused pops.

**Fix:** Set `force-quantum = 1024` at runtime via:
```bash
pw-metadata -n settings 0 'clock.force-quantum' 1024
```
This locked the buffer size, eliminating quantum-change crackles. Also changed resampler from `soxr-vhq` to `soxr-mq` to reduce CPU load (config change, needs PipeWire restart).

The runtime `pw-metadata` approach applies immediately without restart — useful for testing before committing to config changes.

[[pipewire-config-chaos-quantum-conflicts]] [[audio-crackling]] [[pipewire-runtime-tuning]]
