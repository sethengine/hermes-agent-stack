---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-15"
category: audio
related: [pipewire, alc1220, crackling, deepfilternet, resampler, soxr, quantum, easyeffects]
---

# PipeWire ALC1220 Research-Validated Optimal Config

Cross-verified research synthesis confirming the optimal PipeWire configuration for Realtek ALC1220 (Gigabyte Z890 AERO G) with EasyEffects + DeepFilterNet chain.

## Key Findings

### Format: S32LE only
ALC1220 hardware only supports S16_LE and S32_LE natively (`aplay -D hw:1 --dump-hw-params` confirms). S24_LE is NOT listed despite the codec dump showing `bits 16 20 24 32`. F32LE is rejected by the hardware adapter. PipeWire's internal graph always uses F32P regardless — the F32P→S32LE conversion costs negligible CPU.

### Resampler: soxr-mq is transparent
soxr claims "bit-perfect within practical occupied-bandwidth limits" even at default quality per the soxr README. soxr-vhq uses 3-5× the CPU of soxr-mq for SNR ~175dB vs ~140dB — both far beyond human hearing (~96dB CD quality). The CPU savings from soxr-mq go to DeepFilterNet where they matter more.

### Quantum: 1024 locked
Fixed quantum eliminates quantum-adaptation pops. 1024 = ~21ms at 48kHz — imperceptible for wired headphones/non-gaming. `clock.force-quantum` prevents the adapter from switching quantum sizes.

### ALSA path: front:1 correct
`front:1` and `hw:1` use identical DAC hardware. `front:1` avoids device conflict with the auto-detected alsa_output sink.

## Recommended Final Config

| Setting | Value | Why |
|---------|-------|-----|
| `audio.format` | S32LE | Only 32-bit format hardware supports |
| `resample.method` | soxr-mq | Transparent, saves CPU for DeepFilterNet |
| `clock.quantum` | 1024 (locked) | No adaptation pops, enough for EE chain |
| `api.alsa.path` | front:1 | Same quality as hw, avoids device conflict |
| `api.alsa.period-size` | 512 | Proven stable per hw_params |
| `node.suspend` | false | Prevents codec volume reset |

## DeepFilterNet Crackling Diagnostic

Residual crackling after all config fixes (quantum, resampler, ALSA path) is likely from **DeepFilterNet neural net inference causing sporadic CPU spikes** on Arrow Lake P-cores. The denoiser runs real-time inference per audio frame — if a frame takes longer than the period budget (~10.6ms at 48kHz/512), a crackle results. This is _not_ a PipeWire config issue.

**Try:** Bypass DeepFilterNet in EasyEffects and see if crackling stops. If so, the fix is either a more efficient denoiser or CPU frequency pinning.

[[pipewire-quantum-crackle-fix]] [[pipewire-config-chaos-quantum-conflicts]] [[alc1220-sof-vs-hda-driver-conflict]] [[easyeffects-pipewire-restart-crash]] [[audio-underrun]]
