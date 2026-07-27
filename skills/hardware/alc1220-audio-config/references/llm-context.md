# LLM Context — ALC1220 Audio Config

When asked about audio issues on this system, read `SKILL.md` first. Contains all 6 known issues.

## System
- Motherboard: Gigabyte Z890 AERO G
- Audio codec: Realtek ALC1220 (HDA Intel PCH, card 1)
- GPU audio: NVIDIA GB206 (card 0)
- DSP driver: `snd_intel_dspcfg/dsp_driver=1` (legacy HDA)
- Audio server: PipeWire 1.6.5 + WirePlumber 0.5.14
- Headphones: Sony WH-1000XM3 via aux cable → Douk Audio amp → rear line-out
- Kernel: Manjaro 7.0.x (Linux 7.0.10-1-MANJARO)

## Format Rules (CRITICAL — breaking these crashes PipeWire)
- `adapter` `args` block → `audio.format = S32LE` (no underscore, no quotes needed)
- `context.properties` → `default.audio.format = "F32_LE"` (underscore OK here)
- `factory.name` MUST be quoted: `factory.name = "api.alsa.pcm.sink"`
- ALC1220 DAC only supports integer PCM (16/20/24/32 bit). F32LE in adapter args = crash.

## Config File Locations
- `~/.config/pipewire/pipewire.conf`
- `~/.config/pipewire/pipewire.conf.d/99-audio-quality.conf`
- `~/.config/pipewire/pipewire.conf.d/alsa-sink-alc1220.conf`
- `~/.config/pipewire/pipewire.conf.d/alsa-sink-gb206.conf`
- `/etc/modprobe.d/snd-intel-dspcfg.conf`
- `/etc/modprobe.d/snd-hda-intel.conf`
- `~/.config/systemd/user/alc1220-audio.service`
- `~/.local/bin/restore-alc1220.sh`
- `~/.config/easyeffects/db/easyeffectsrc`

## Common Mistakes
1. `amixer -c1 set Headphone 87` — does NOT actually change hardware. Use `cset numid=3 87,87`
2. `dsp_driver=3` on Arrow Lake → SOF fails, device orphaned. Use `dsp_driver=1`
3. `audio.format = F32LE` in adapter args → ALC1220 doesn't support float
4. Default quantum=256 → underruns with EE+DeepFilterNet. Use quantum=1024

## GitHub Repo
https://github.com/sethengine/alc1220-audio-config
(contains exact config files + full skill documentation)
