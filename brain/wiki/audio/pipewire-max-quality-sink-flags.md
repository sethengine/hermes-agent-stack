---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-18"
category: audio
related: [pipewire, alc1220, resample, channelmix, priority, soft-mixer]
---

# PipeWire Max-Quality Sink Config Flags

Beyond the core format/resampler/quantum settings, additional config flags maximize audio quality on ALC1220.

## Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| `resample.disable` | `true` | Bypass SRC entirely. All sources are 48kHz, so resampler never fires anyway — this locks the guarantee. |
| `monitor.channel-volumes` | `false` | Clean signal path, no per-channel volume processing |
| `channelmix.upmix` | `false` | No stereo-to-surround smearing |
| `channelmix.mix-lfe` | `false` | No subwoofer processing on non-LFE content |
| `channelmix.normalize` | `false` | Don't touch levels automatically |
| `api.alsa.soft-mixer` | `true` | Software volume — ALSA codec hardware mixer state becomes irrelevant (fixes volume reset on PW restart) |
| `priority.driver` | `9000` | Custom sink wins over auto-detected sinks |
| `priority.session` | `9000` | Same for session priority |

These complement `node.suspend = false` (already documented) for a fully optimized signal path.

[[pipewire-alc1220-research-validated-config]] [[pipewire-alsa-codec-volume-reset-chain]]
