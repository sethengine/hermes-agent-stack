# Quantum Tuning for Heavy EasyEffects Chains

## Session Context

User with Gigabyte Z890 AERO G (ALC1220) reported periodic crackling/popping every ~2 minutes during playback through an 11-plugin EasyEffects chain including DeepFilterNet.

## Config at Time of Issue

```
~/.config/pipewire/pipewire.conf.d/99-audio-quality.conf:
  default.clock.quantum       = 512    # 10.7ms
  default.clock.min-quantum   = 256    # 5.3ms minimum
```

## Root Cause

PipeWire's adaptive quantum scaled down to 256 frames (5.3ms at 48kHz) during low-load periods. When the system experienced a periodic scheduling spike (page fault, background I/O, DeepFilterNet inference completion), the 5.3ms buffer was consumed before the next quantum's processing cycle completed → crackle/pop (underrun).

The EE chain workload at the time:
- Bass Enhancer (harmonics)
- Bass Loudness (dynamics)
- 2× Equalizers (band EQs)
- Exciter (bypassed but still loaded)
- Crystalizer (bypassed but still loaded)
- 2× more Equalizers (treble cut + warm curve)
- Limiter
- **DeepFilterNet** (neural network inference — primary CPU spike source)
- Stereo Tools
- Format conversion: F32LE (EE internal) → S32LE (ALC1220 hardware)

## Fix

Increased quantum to 1024 (21.3ms) and min-quantum to 512:

```conf
default.clock.quantum       = 1024
default.clock.min-quantum   = 512
default.clock.max-quantum   = 8192
```

Crackling stopped. The 21ms buffer provides 4× the scheduling headroom vs 5.3ms.

## Where the Setting Lives

On this system, the quantum was set in TWO places:
1. `~/.config/pipewire/pipewire.conf` — overridden by...
2. `~/.config/pipewire/pipewire.conf.d/99-audio-quality.conf` — alphabetically last, wins

The `.d/99-*` file was the effective source. Always check the last alphabetically-sorted config file.

## Verification

```bash
pw-metadata -n settings 2>&1 | grep clock
# Should show:
# clock.quantum = 1024
# clock.min-quantum = 512
# clock.max-quantum = 8192
# clock.force-quantum = 0  (0 = adaptive allowed within min/max bounds)
```

## Related

- `/etc/modprobe.d/snd-intel-dspcfg.conf` set to `options snd-intel-dspcfg dsp_driver=1` (legacy HDA, not SOF) — see `z890-ace-audio-diagnostic.md`
- Headphone volume set via `amixer -c1 cset numid=3 87,87` + `numid=4 on,on` — ALSA simple mixer lies on ALC1220
