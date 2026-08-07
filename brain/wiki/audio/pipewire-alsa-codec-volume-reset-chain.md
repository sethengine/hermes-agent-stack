---
source_session: "20260701_184534_aa1b2f"
date: "2026-07-18"
category: audio
related: [pipewire, alc1220, volume-reset, codec, soft-mixer, node-suspend]
---

# ALSA Codec Volume Reset Chain on PipeWire Restart

The ALC1220 headphone hardware mixer (ALSA numid=3) resets to **0/muted** every time PipeWire restarts, because the adapter factory opens the ALSA PCM device, triggering codec hardware initialization.

## Root Cause Chain

```
PipeWire starts → context.exec runs (too early) → adapter opens hw:1
→ codec hardware init resets numid=3 to 0/muted → ensure-volume script already exited
```

The `ensure-alc1220-volume.sh` script runs via `context.exec` but executes **before** the adapter creates the PCM device. By the time the codec resets to 0, the script is done.

## Fix Options

### Option 1: Software mixer (recommended)
`api.alsa.soft-mixer = true` in the sink config. PipeWire handles volume in software — the ALSA codec hardware mixer state (which keeps resetting) becomes irrelevant. Codec always outputs at full volume; PW manages volume by adjusting audio data.

### Option 2: Prevent codec power-cycling
`node.suspend = false` — prevents the adapter from suspending/resuming, which avoids the codec re-init that triggers the volume reset.

Option 1 is more robust as it eliminates ALSA hardware mixer dependency entirely.

[[pipewire-alc1220-research-validated-config]]
