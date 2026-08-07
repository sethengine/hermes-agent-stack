---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-18"
category: audio
related: [easyeffects, eq, tinny-sound, exciter, treble-cut]
---

# EasyEffects Tinny Sound Diagnosis and EQ Fix

Aggressive treble cut in EQ#2 can paradoxically make sound **tinny/hollow** by suppressing air frequencies, causing upper mids (2-5kHz) to dominate by comparison.

## Symptoms

- Sound perceived as tinny, closed, or hollow
- Upper mids poke out harshly
- No air or sparkle in vocals/instruments

## Root Cause

EQ#2 had cuts at -6.5dB to -6.9dB across 8kHz-11kHz. This excessive cut kills all air frequencies, making upper mids sound dominant and creating the tinny perception.

## Fix

| Setting | Before | After | Why |
|---------|--------|-------|-----|
| EQ#2 8kHz cut | -6.75dB | **-4.5dB** | Less aggressive cut restores air |
| EQ#2 10kHz cut | -6.5dB | **-4.5dB** | Same — balanced with Exciter |
| EQ#2 11kHz cut | -6.93dB | **-4.5dB** | Same |
| Exciter | bypassed | **enabled at 2.0** | Adds presence without harshness |

## Balancing with Exciter

Enabling Exciter adds treble harmonics that can overshoot. If still sharp after reducing cuts:
- Increase EQ#2 cuts slightly (to -4.5dB) to tame Exciter harmonics
- Lower Exciter `amount` or `harmonics` if EQ alone doesn't fix

The previous -6.5dB cut was so aggressive that the upper mids (2-5kHz) dominated by comparison. Reducing to -4.5dB and enabling the Exciter at a mild setting restores air without harshness.

[[easyeffects-exciter-configuration]] [[pipewire-alc1220-research-validated-config]]
