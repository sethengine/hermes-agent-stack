---
source: "20260718_002551_e88b73"
date: "2026-07-18"
category: "audio"
tags: [easyeffects, pipewire, audio-processing, equalizer, bass-enhancer]
---

# EasyEffects Active Processing Chain

## Overview

EasyEffects output chain has 12 plugins installed but only **4 active**. The effective signal path is a stripped-down warmth-and-bass-tuning chain on [[pipewire-sink-configuration]].

## Active Plugins

| Order | Plugin | Settings |
|-------|--------|----------|
| 1 | **Bass Enhancer** | amount=6.06, floor=23Hz, harmonics=1, inputGain=-4.05dB |
| 2 | **Equalizer #0** | Sub-bass shelf (6 bands): 25Hz(+3.2), 45Hz(+5.7), 65Hz(+4.9), 85Hz(+1.5), 105Hz(+0.1) |
| 3 | **Equalizer #2** | High cut: 8kHz(-6.75), 10kHz(-6.5), 11kHz(-6.93) — tames harsh highs |
| 4 | **Equalizer #3** | Presence/warmth: 80Hz(+2), 250Hz(+3.5), 500Hz(+1.5), 2kHz(-0.5), 6kHz(-1.5) |

**Effective chain**: `Bass Enhancer → Sub-bass EQ → 8-11kHz cut → Warmth EQ`

Tuned for Sony XM3 headphones via Douk amp — sub-bass emphasis + harshness rolloff.

## Bypassed Plugins

- Bass Loudness
- Crystalizer
- DeepFilterNet (×3 instances)
- Equalizer #1 (gain=+13.8dB sitting unused)
- Exciter
- Limiter
- Pitch
- Stereo Tools

These are present in the pipeline config (`~/.config/easyeffects/output/`) but have `bypass=true`. They can be re-enabled without reconfiguration.

## Tuning Rationale

- Sub-bass EQ (+3.2 to +5.7dB from 25–65Hz) compensates for open-back headphone rolloff
- 8–11kHz cut (-6.5 to -6.93dB) reduces sibilance and harshness from lossy codecs
- Presence shelf (+2dB @ 80Hz, +3.5 @ 250Hz) adds warmth without muddiness
- Bass Enhancer harmonics add psychoacoustic low-end extension
