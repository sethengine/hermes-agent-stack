# EasyEffects Game Audio Blocklist

## Problem

EasyEffects' DSP processing chain adds 5-15ms of filter latency to all audio passing through it. In competitive gaming (Dota 2, shooters, etc.), this latency is noticeable and degrades audio responsiveness (footsteps, spell cues, spatial awareness).

EasyEffects processes ALL audio going to the configured output device by default. Games cannot be excluded unless they use a different audio device entirely (e.g., HDMI audio from GPU directly to monitor speakers).

## Solution: application blocklist

EasyEffects supports per-application exclusion via the blocklist: `~/.config/easyeffects/blocklist.json`. Applications on the blocklist bypass the entire DSP chain — audio flow goes directly from the application to the output device without passing through any EasyEffects plugins.

### Blocklist file location

```
~/.config/easyeffects/blocklist.json
```

### Recommended blocklist entries for gaming

```json
[
  "dota2",
  "steam",
  "steamwebhelper"
]
```

`"steam"` and `"steamwebhelper"` catch the Steam client UI sounds and browser-based audio. `"dota2"` matches the Dota 2 process.

### How it works

- EasyEffects matches applications by their binary/window name (Wine/Proton games use their native binary name)
- Blocklisted applications bypass the `easyeffects_sink` entirely and route directly to the physical output device
- EasyEffects processes non-blocklisted applications normally (music, browser, voice chat)
- No audio routing changes needed — `pactl` configuration stays the same

### Verification

```bash
# Check blocklist is loaded
cat ~/.config/easyeffects/blocklist.json

# Verify game audio bypasses EE
# Start the game, then check:
pactl list short sink-inputs

# Game's sink-input should be connected to the physical sink,
# not to easyeffects_sink
```

### Limitations

- Per-application blocklist granularity: EasyEffects blocks by binary name, not by specific audio stream. All audio from the blocklisted app is unprocessed.
- No per-application toggle in EE GUI (config file only)
- Requires EE restart to reload blocklist after editing

## Trade-offs

- **Without blocklist:** Full DSP chain applies to everything — better music/movie audio, worse game latency
- **With blocklist:** Games get raw audio (no EQ, no compression, no spatial processing), music/apps still benefit from DSP
- **Compromise:** Disable CPU-heavy plugins (DeepFilterNet, Crystalizer) instead of blocking games — reduces latency by 5-10ms while keeping basic EQ

## Related

- Brain wiki: `software/easyeffects-game-audio-blocklist.md`
- EE plugin chain: `skill_view(name=pipewire-audio, file_path=references/ee-plugin-chain-sizing.md)`
- PipeWire quantum tuning for latency vs stability: See pipewire-audio SKILL.md → PipeWire Quantum / Buffer Tuning
