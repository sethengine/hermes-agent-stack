# ALC1220 Dual-DAC Routing & systemd Persistence

## ALC1220 Codec Audio Path (Gigabyte Z890 AERO G, Subsystem 0x1458a0c3)

The ALC1220 has **two independent DACs** — one for Line Out (rear panel), one for Headphone (front panel), each with its own mixer and pin complex.

### DAC → Mixer → Pin Routing

```
Node 0x02 (Line Out DAC) → Node 0x0c (mixer, src 1=0x02) → Node 0x14 (pin, Line Out Rear)
Node 0x03 (Headphone DAC) → Node 0x0d (mixer, src 1=0x03) → Node 0x1b (pin, HP Out Front)
```

### Pin Complexes

| Node | Function | Pin Default | Connection | EAPD |
|------|----------|-------------|------------|------|
| 0x14 | Line Out Rear (green) | `0x01014010` | 0x0c | 0x2 (enabled) |
| 0x1b | HP Out Front (green) | `0x02214020` | 0x0d* | 0x2 (enabled) |
| 0x18 | Mic Rear (pink) | `0x01a19040` | 0x0c* | — |
| 0x19 | Mic Front (pink) | `0x02a1904f` | 0x0c* | — |
| 0x15-17 | Unused N/A rear jacks | `0x411111f0` | 0x0d/0e/0f | — |

Note: `*` marks the active connection in the pin's connection list.

### Mixer Details

```
Node 0x0c: Amp-In [0x00 0x00] [0x80 0x80]  ← src 0 (0x02) unmuted, src 1 (0x0b) muted
Node 0x0d: Amp-In [0x00 0x00] [0x80 0x80]  ← src 0 (0x03) unmuted, src 1 (0x0b) muted
```

`[0x00 0x00]` = unmuted (stereo), `[0x80 0x80]` = muted (bit 7 set).

### DACs

| Node | Control Name | Amp-Out Range | Stream |
|------|-------------|---------------|--------|
| 0x02 | Line Out Playback Volume | 0-87 (0x57) | stream=1, channel=0 |
| 0x03 | Headphone Playback Volume | 0-87 (0x57) | stream=1, channel=0 |

Both DACs share `stream=1, channel=0` — they receive the same audio data. The volume difference between Line Out and Headphone is purely analog attenuation at the DAC node.

### Pin Control Values

- `0x40` = OUT (line-level output)
- `0xc0` = OUT | HP (headphone amp enabled)
- `0x20` = IN (input — used for unused jacks/mics)
- `0x24` = IN | VREF_80 (microphone with 80% bias voltage)

### ALSA Mixer Controls

| numid | Name | Node | Function |
|-------|------|------|----------|
| 1 | Line Out Playback Volume | 0x02 | Rear green jack volume |
| 2 | Line Out Playback Switch | 0x14 | Rear green jack mute |
| 3 | Headphone Playback Volume | 0x03 | Front green jack volume |
| 4 | Headphone Playback Switch | 0x1b | Front green jack mute |
| 20 | Master Playback Volume | 0x01 (AFG) | Global mono volume (joined) |
| 27 | Playback Channel Map | PCM | FL=3, FR=4 (stereo) |

### The Simple Mixer Lie

When Auto-Mute Mode is ENABLED (default), plugging headphones into the front jack should:
1. Mute the Line Out (rear)
2. Unmute the Headphone output
3. Switch Headphone volume to active controls

However, on some ALC1220 implementations (Gigabyte Z890 AERO G confirmed), the `amixer` simple mixer control `Headphone` and the actual hardware register `numid=3 Headphone Playback Volume` are **not the same object**. The simple mixer can show `87,87 [on,on]` while `amixer -c1 cget numid=3` reports `values=0,0` and `amixer -c1 cget numid=4` reports `values=off,off`.

**Always use direct numid access**:
```bash
amixer -c1 cset numid=3 87,87    # Headphone Playback Volume → 100% both channels
amixer -c1 cset numid=4 on,on    # Headphone Playback Switch → unmuted both channels
```

## Persistence Model

### Problem
- numid settings reset to 0 on PipeWire restart (any reason — crash, config reload, dsp_driver change)
- `pactl set-default-sink` is ephemeral — lost on restart
- `pactl suspend-sink` is ephemeral
- `alsactl store` captures mixer state but PipeWire's ALSA plugin resets on open

### Solution: systemd user service

File: `~/.config/systemd/user/alc1220-audio-fix.service`

```ini
[Unit]
Description=ALC1220 Audio Fix
Wants=pipewire.service wireplumber.service pipewire-pulse.service
After=pipewire.service wireplumber.service pipewire-pulse.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/usr/bin/sleep 5
ExecStart=/usr/bin/amixer -c1 cset numid=3 87,87
ExecStart=/usr/bin/amixer -c1 cset numid=4 on,on
ExecStartPost=/bin/sh -c '/usr/bin/pactl set-default-sink alc1220-analog-sink || true'
ExecStartPost=/bin/sh -c '/usr/bin/pactl set-sink-volume alc1220-analog-sink 100% || true'
ExecStartPost=/bin/sh -c '/usr/bin/pactl suspend-sink alsa_output.pci-0000_80_1f.3.analog-stereo 1 || true'

[Install]
WantedBy=default.target
```

Install:
```bash
systemctl --user daemon-reload
systemctl --user enable alc1220-audio.service
```
*Note: `Wants=` soft dependency prevents chain-failure when pipewire is in start-limit-hit. `WantedBy=default.target` runs at session start regardless of pipewire lifecycle state. pactl commands use `|| true` to swallow failures gracefully.*

### Verification

```bash
systemctl --user is-active alc1220-audio-fix.service
amixer -c1 cget numid=3   # should show 87,87
pactl info | grep 'Default Sink'  # should show alc1220-analog-sink
```
