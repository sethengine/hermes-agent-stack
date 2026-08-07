---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-18"
category: audio
related: [easyeffects, exciter, plugin-chain, sound-quality]
---

# EasyEffects Exciter Plugin Configuration

The Exciter plugin adds harmonic content for presence and air. On ALC1220 with Sony XM3 (via Douk amp), conservative settings avoid harshness.

## Recommended Conservative Settings

| Parameter | Value | Why |
|-----------|-------|-----|
| `amount` | **2.0** (range 0-10) | Below default 3.42 — less aggressive |
| `harmonics` | **2.0** (range 1-10) | Cleaner; low harmonics add fundamental, not harsh upper harmonics |
| `blend` | **2.0** (range 0-10) | Less wet signal; lets original through more |
| `bypass` | `false` | Now active |

## Current Plugin Chain (active only)

```
Bass Enhancer → EQ#0 (bass boost) → Bass Loudness (bypassed) →
EQ#2 (treble cut) → EQ#3 (warmth) → Limiter
```

## Interaction with EQ#2

Exciter adds treble harmonics that can clash with the treble cut EQ. When enabling Exciter:
- If sound becomes sharp/harsh → slightly increase EQ#2 cut (e.g., from -3dB to -4.5dB)
- If sound becomes dull → slightly decrease EQ#2 cut
- Balance is iterative: Exciter adds, EQ#2 subtracts

[[easyeffects-tinny-sound-eq-fix]] [[easyeffects-crash-missing-sink]]
