# Sony WH-1000XM3 Passive Mode — Diagnostic Reference

## The Core Issue

The WH-1000XM3's 40mm drivers are **tuned exclusively around active DSP correction**. When used via aux cable with the headphones **powered off** (passive mode), the raw driver frequency response is objectively poor:

| Frequency Range | Behavior | Perceptual Effect |
|----------------|----------|-------------------|
| < 100 Hz | Bass drops off steeply | No sub-bass, no body |
| 200–400 Hz | Recessed lower-mids | Thin, hollow vocals |
| 8–10 kHz | Raw driver peaks | Harsh, tinny treble |

This produces exactly the "tin can" / "hollow" / "thin" sound that users describe.

## First Diagnostic Question

When user reports "tinny" / "thin" / "hollow" sound via aux:

> **Are the headphones powered ON when using the aux cable?**

Powering them on (even with NC/Ambient set to OFF) engages the internal DSP which corrects the passive frequency response. This fixes ~99% of complaints.

## Verification Steps

```bash
# 1. Check if headphones are in passive mode
# → User confirms they hear sound but it's thin/tinny

# 2. Rule out PipeWire/EasyEffects causing the issue
# Bypass EasyEffects entirely
pactl set-default-sink alsa_output.pci-0000_80_1f.3.analog-stereo

# If still tinny after switching sinks, it's NOT the DSP chain

# 3. Test with ALSA directly (bypasses PipeWire entirely)
systemctl --user stop pipewire wireplumber 2>/dev/null
speaker-test -c2 -D plughw:1,0 --test=wav -l1

# 4. Confirm ALSA hardware parameters
cat /proc/asound/card1/pcm0p/sub0/hw_params
# Expected: format: S32_LE, channels: 2, rate: 48000
```

## EasyEffects Chain That Sounds Warm (Not Tinny)

If user insists the chain is causing the problem and headphones ARE powered on, this EQ compensates the XM3's residual DSP deficiencies:

| Band | Gain | Type | Q | Target |
|------|------|------|---|--------|
| 80Hz | +2.0dB | Low Shelf | 0.707 | Add sub-bass body |
| 250Hz | +3.5dB | Peak | 0.8 | Fill hollow lower-mids |
| 500Hz | +1.5dB | Peak | 0.7 | Smooth transition |
| 2kHz | -0.5dB | Peak | 1.0 | Calm upper-mid presence |
| 6kHz | -1.5dB | Peak | 1.0 | Pre-smooth before treble cut |
| 8.2kHz | -3.0dB | Peak | 3.0 | Tame 8kHz XM3 peak |

Note: The Exciter (if enabled) adds harmonics that can sound harsh on these headphones — check `bypass=true` in exciterrc.
The Crystalizer adds high-frequency detail — check `bypass=true` in crystalizerrc if treble is harsh.
