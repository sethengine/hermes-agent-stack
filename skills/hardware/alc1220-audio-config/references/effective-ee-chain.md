# Effective EasyEffects Chain (Current)

Audited 2026-07-18. Plugin chain from `~/.config/easyeffects/db/easyeffectsrc`:

```
plugins=bass_enhancer#0,equalizer#0,bass_loudness#0,equalizer#1,pitch#0,exciter#0,crystalizer#0,equalizer#2,equalizer#3,limiter#0,deepfilternet#0,stereo_tools#0
```

## Bypass State

| # | Plugin | Bypass | Notes |
|---|--------|--------|-------|
| 1 | Bass Enhancer #0 | **ACTIVE** | amount=8.01, floor=23, harmonics=1, inputGain=-8.1 |
| 2 | Equalizer #0 | **ACTIVE** | 6-band sub-bass shelf: 25Hz(+3.2), 45Hz(+5.7), 65Hz(+4.9), 85Hz(+1.5), 105Hz(+0.1) |
| 3 | Bass Loudness #0 | bypassed | loudness=-7.1 |
| 4 | Equalizer #1 | bypassed | outputGain=+13.8 (gain stage, unused) |
| 5 | Pitch #0 | bypassed | — |
| 6 | Exciter #0 | **ACTIVE** | amount=2.0, harmonics=2.0, blend=2 — moderate presence enhancement |
| 7 | Crystalizer #0 | bypassed | — |
| 8 | Equalizer #2 | **ACTIVE** | 8kHz(-6.75), 10kHz(-6.5), 11kHz(-6.93) — treble cut |
| 9 | Equalizer #3 | **ACTIVE** | 80Hz(+2), 250Hz(+3.5), 500Hz(+1.5), 2kHz(-0.5), 6kHz(-1.5) — warmth/balance |
| 10 | Limiter #0 | bypassed | attack=1ms, release=20ms, inputGain=+1.8 (tuned but off) |
| 11 | DeepFilterNet #0,1,2 | bypassed | — |
| 12 | Stereo Tools #0 | bypassed | — |

## Effective Processing Path

```
App → easyeffects_sink
  → Bass Enhancer (active bass harmonics)
  → EQ#0 (sub-bass shelf — low-end body)
  → Exciter (moderate presence enhancement)
  → EQ#2 (8-11kHz cut — tame treble harshness)
  → EQ#3 (warmth curve — fill lower-mids, smooth presence)
  → alc1220-analog-sink
```

**5 of 12 plugins active.** The remaining 7 are bypassed.
