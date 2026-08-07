---
source_session: "20260709_193718_2e6307"
date: "2026-07-09"
category: audio
related: [pipewire, quantum, latency, crackling]
---

# PipeWire Config Chaos — Quantum Conflicts

Four PipeWire configs were setting different quantum values:

| Config | quantum | min-quantum | force-quantum |
|--------|---------|-------------|---------------|
| `99-audio-quality.conf` | 1024 | 512 | **1024** |
| `99-high-quality.conf` (pulse) | 512 | 64 | — |
| `99-low-latency.conf` (pulse) | 1024 | 256 | — |
| `alsa-sink-alc1220.conf` | period-size=512 | — | — |

`force-quantum=1024` in `99-audio-quality.conf` won → **21.3ms audio latency at 48kHz**. ALSA period (512) vs graph quantum (1024) mismatch wasted the hardware buffer. Resampler was `soxr-vhq` (very high CPU).

**Fix:** Remove conflicting configs, set clean 512 quantum.

[[pipewire-config]] [[audio-latency]] [[audio-crackling]]
