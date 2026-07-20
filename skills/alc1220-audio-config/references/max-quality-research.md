# Maximum Quality Config — Research Sources

Compiled 2026-07-18 from deep-research protocol (cross-verified across 3+ sources).

## Format Selection

### Finding
ALC1220 DAC is a 24-bit converter. S32LE transport is optimal. F32 internal processing loses no audible information — F32 mantissa (24-bit) covers all 2^24 integer values that any DAC on the market (ESS, AKM, TI, Cirrus) sees.

### Sources
1. ASR Bit-Perfect Guide: "every DAC chip on the market is a 24-bit converter. They accept S32LE as a container, but only the top 24 bits reach the core."
2. Arch Linux Forum: `aplay -D hw:1 --dump-hw-params` on ALC1220 shows FORMAT: S16_LE S32_LE only — no S24_LE.
3. PipeWire official docs: adapter format negotiation matches hardware caps.

### Verdict
S32LE is correct. No higher-quality format exists for this hardware.

## Resampler (soxr)

### Finding
`resample.disable = true` when source and sink rates match. soxr at quality 14+ achieves >140dB SNR — audibly transparent. But avoiding SRC entirely is always better.

### Sources
1. ASR: "PipeWire's SoXR resampler at quality 15, and 32-bit float internal processing with dithered output, are arguably transparent in controlled ABX testing."
2. soxr README: "Bit-perfect within practical occupied-bandwidth limits."
3. PipeWire props docs: resample.quality range 0-14 (official) or 0-15 (pw-cat).

### Verdict
Lock all rates to 48kHz and set `resample.disable = true`. If resampling is unavoidable, `resample.quality = 14` is the ceiling.

## Channelmix

### Finding
`channelmix.upmix=true` (PipeWire default) upmixes stereo to multi-channel, smearing the stereo image. For pure stereo output, disable all channelmix modifications.

### Sources
1. PipeWire official config docs: defaults show upmix=true, mix-lfe=true.
2. ASR guide: sets `channelmix.normalize=false, upmix=false, mix-lfe=false`.

### Verdict
Set all to false for stereo hifi use.

## Quantum

### Finding
1024 frames at 48000Hz = 21.3ms. Low enough to be imperceptible, high enough to prevent xruns with heavy DSP chains. Lock with `clock.force-quantum = 1024`.

### Sources
1. ASR guide: uses default.clock.quantum = 1024.
2. Practical testing on this system: quantum=256 caused crackling with EE+DeepFilterNet.

### Verdict
1024 locked. No lower.

## ALSA Path

### Finding
`hw:1` bypasses ALSA plug layer (bit-perfect path). `front:1` adds plug layer (format conversion, channel remapping). For S32LE where both produce identical output, `front:1` avoids device conflict with auto-detected sink. No quality difference.

### Sources
1. ASR: "hw:USB — ALSA hardware path, direct access, no plugins."
2. hw_params confirmed format: S32_LE with both paths.

### Verdict
front:1 is fine. No quality loss vs hw:1.
