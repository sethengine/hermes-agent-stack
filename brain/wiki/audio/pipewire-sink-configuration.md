---
source: "20260718_002551_e88b73"
date: "2026-07-18"
category: "audio"
tags: [pipewire, sinks, alc1220, audio-config, easyeffects]
---

# PipeWire Sink Configuration — ALC1220

## Sink Layout

| Sink | State | Format | Purpose |
|---|---|---|---|
| **alc1220-analog-sink** (custom) | RUNNING | s32le 2ch 48kHz | Default — ALC1220 → Douk amp → Sony XM3 |
| **easyeffects_sink** | RUNNING | float32le 2ch 48kHz | EasyEffects processing loopback |
| alsa_output.pci-0000_02_00.1.pro-output-3 | SUSPENDED | s32le 2ch 48kHz | NVIDIA HDMI (GPU audio) |
| alsa_output.pci-0000_80_1f.3.analog-stereo | SUSPENDED | s32le 2ch 48kHz | Intel/ACE motherboard audio |
| pro-output-7/8/9 | SUSPENDED | s32le 8ch 48kHz | Additional NVIDIA HDMI |

## PipeWire Config (`~/.config/pipewire/pipewire.conf.d/`)

| Setting | Value |
|---|---|
| ALSA path | `front:1` (hw:1 — ALC1220) |
| Format | S32LE 2ch |
| Rate | 48000 (locked, no fallback) |
| Resample quality | `soxr-vhq` |
| Period-size | 256 frames × 3 periods = 768 frames ring buffer |
| Quantum | 512 (default), min 256, max 1024 |

## Notes

- `front:1` uses the ALC1220's analog output only (bypasses digital/HDMI paths)
- S32LE → float32 conversion happens transparently in PipeWire's graph
- Quantum of 512 frames at 48kHz ≈ 10.7ms DSP block — reasonable [[linux-latency-tuning]] target
- Unused HDMI/ACE sinks stay SUSPENDED by default (power saving)
- [[easyeffects-processing-chain]] routes through `easyeffects_sink` → `alc1220-analog-sink`
