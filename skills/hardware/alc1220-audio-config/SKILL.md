---
name: alc1220-audio-config
description: Complete audio configuration for Gigabyte Z890 AERO G with Realtek ALC1220 + Sony WH-1000XM3 on Manjaro Linux
---

# ALC1220 Audio Configuration — Gigabyte Z890 AERO G

## Hardware Chain
```
PC → ALC1220 analog line-out → Douk Audio amp → Sony WH-1000XM3 (aux cable, powered ON)
```

## Reference Files
This skill ships with:
- `references/error-transcripts.md` — exact dmesg, pw-dump, coredump, and ALSA codec transcripts from real debugging sessions
- `references/llm-context.md` — condensed LLM-facing quick-reference for other AI agents
- `references/effective-ee-chain.md` — current EasyEffects bypass-state audit and effective processing path (updated 2026-07-18)

## Config Files Located

| File | Purpose |
|------|---------|
| `~/.config/pipewire/pipewire.conf` | Main PipeWire daemon config |
| `~/.config/pipewire/pipewire.conf.d/99-audio-quality.conf` | Audio quality overrides (quantum, resampler) |
| `~/.config/pipewire/pipewire.conf.d/alsa-sink-alc1220.conf` | Custom ALC1220 analog sink (adapter factory) |
| `~/.config/pipewire/pipewire.conf.d/alsa-sink-gb206.conf` | Custom GB206 (NVIDIA) HDMI audio sink (may be disabled) |
| `/etc/modprobe.d/snd-intel-dspcfg.conf` | DSP driver selection |
| `/etc/modprobe.d/snd-hda-intel.conf` | HDA driver tuning |
| `~/.config/systemd/user/alc1220-audio.service` | Persistence service (headphone volume + default sink) |
| `~/.local/bin/restore-alc1220.sh` | ALSA mixer restore script |
| `~/.config/easyeffects/db/easyeffectsrc` | EasyEffects chain config |

## Known Issues & Fixes

### 1. Intel Audio Card Not Detected
**Symptom:** `aplay -l` shows only NVIDIA HDMI, no Intel PCH
**Cause:** `dsp_driver=3` (auto) → SOF driver grabs Intel audio → DSP not enabled in BIOS → device orphaned
**Fix:** `/etc/modprobe.d/snd-intel-dspcfg.conf`:
```
options snd-intel-dspcfg dsp_driver=1
```
Then `sudo mkinitcpio -P && sudo reboot`

### 2. PipeWire Crashing on Startup (status 234)
**Symptom:** `mod.adapter: usage: node.name=<string>` error
**Cause:** Unquoted `factory.name = api.alsa.pcm.sink` in `~/.config/pipewire/pipewire.conf.d/*.conf` — dots in the value break PipeWire's config parser. Also, `F32LE` format in adapter args fails because ALC1220 hardware only supports integer formats.
**Fix:** Quote factory names and use S32LE (no underscore, no quotes):
```ini
factory.name     = "api.alsa.pcm.sink"
audio.format     = S32LE
```

### 3. Right Channel Silence on Headphones
**Symptom:** Only left channel audible, or both channels play same signal
**Cause:** `Headphone Playback Volume` (numid=3) at 0 and `Headphone Playback Switch` (numid=4) off. The ALSA simple mixer `amixer set Headphone` command lies — must use numid directly.
**Fix:**
```bash
amixer -c1 cset numid=3 87,87
amixer -c1 cset numid=4 on,on
```

### 4. Tinny/Hollow Sound on XM3 Headphones
**Symptom:** Audio sounds like "tin can", no bass, thin
**Cause #1:** Sony WH-1000XM3 in PASSIVE mode (powered off via aux cable). The XM3 drivers have a broken frequency response without DSP correction — bass drops below 100Hz, mids are scooped, treble peaks.
**Fix #1:** Turn headphones ON when using aux cable. The internal DSP corrects the response. Can set NC/Ambient to OFF to save battery.
**Cause #2 (if already on):** EasyEffects Exciter or Crystalizer overdrive
**Fix #2:** Check Exciter/Crystalizer bypass state in EE. Check EQ cuts.

### 5. Periodic Crackling/Popping Every Few Minutes
**Symptom:** Audio crackles/glitches once every 1-2 minutes
**Cause:** `default.clock.quantum = 256` (5.3ms buffer) too small for the 11-plugin EasyEffects chain including DeepFilterNet neural net. Underruns on any scheduling jitter.
**Fix:** Increase quantum in `99-audio-quality.conf`:
```ini
default.clock.quantum       = 1024   # 21ms buffer
default.clock.min-quantum   = 512
default.clock.max-quantum   = 8192
```

### 6. EasyEffects Crashes (SIGABRT, lsp-plugins-lv2.so)
**Symptom:** EasyEffects dumps core, `liblsp-plugins-lv2.so` in stack trace along with `libpipewire-module-protocol-native.so`
**Cause:** LSP plugin in the EE chain crashes when PipeWire connection is unstable. Usually secondary to PipeWire config issues (see #2).
**Fix:** Fix PipeWire config first (see #2), then restart EE. If persistent, check which LSP plugin is causing it and update it.

### 7. Volume Resets to 0 After Idle/Pause (Suspend/Resume Bug)
**Symptom:** Audio works during first playback. After all streams stop and restart, headphone volume is 0 and no sound comes out.
**Root cause:** When PipeWire suspends an idle ALSA node, the codec powers down and reinitializes with default mixer state (headphone = muted). On resume, the default state (volume=0) is restored, not the user's setting.
**Fix (three options, best first):**

**Option A — Software mixer (recommended):** Add `api.alsa.soft-mixer = true` to the alc1220 sink adapter args. PipeWire handles volume in software — ALSA hardware mixer state is irrelevant and the headphone mute register can stay at 0 without affecting playback. No retry scripts needed.

**Option B — Prevent suspend:** Add `node.suspend = false` to the adapter args so the ALSA device never suspends. Volume stays set because the codec never powers down.

**Option C — Retry script:** If using context.exec, the adapter opens the ALSA device AFTER exec runs, so any amixer commands execute too early. Use a retry loop:
```bash
# ~/.local/bin/ensure-alc1220-volume.sh
for i in $(seq 1 30); do
    /usr/bin/amixer -c1 cset numid=3 87,87 2>/dev/null
    /usr/bin/amixer -c1 cset numid=4 on,on 2>/dev/null
    STATUS=$(/usr/bin/amixer -c1 cget numid=3 2>/dev/null | grep -c 'values=87,87')
    [ "$STATUS" -gt 0 ] && exit 0
    sleep 1
done; exit 1
```
Then in `pipewire.conf context.exec`:
```ini
{ path = "/home/sethengine/.local/bin/ensure-alc1220-volume.sh" args = "" }
```

**Workflow warning:** Do NOT restart pipewire repeatedly to test volume fixes — each restart triggers the adapter to reopen the ALSA device, resetting the codec again. Use direct `amixer` commands on the live system for volume changes. Only restart pipewire when changing adapter config files that require it.

## ALSA Hardware Specs

Realtek ALC1220 (Subsystem: 0x1458a0c3 — Gigabyte Z890 AERO G):
- DAC: bits 16/20/24/32 (integer only, no float)
- Rates: 44100-192000
- Cards: `0 [NVidia]` HDMI, `1 [PCH]` analog
- Headphone DAC: Node 0x03 (separate from Line Out Node 0x02)
- Line Out: Node 0x14 (rear green jack)
- Headphone Out: Node 0x1b (front panel)

## Current working format chain:
```
App → EE (F32P) → PW auto-convert → alc1220-sink (S32LE) → ALC1220 DAC
```
PipeWire handles the F32P→S32LE conversion at the graph level. HW params confirm `format: S32_LE` at the ALSA level.

## PipeWire/ALSA Tuning Notes
- `threadirqs` in kernel cmdline — threaded IRQs for audio
- `rt.prio = 88` in PipeWire RT module
- `power_save=0` for snd_hda_intel — no power saving on audio
- `Auto-Mute Mode` should be Enabled (mutes line out when headphones plugged in)
- `resample.quality = 10` (soxr-vhq) in `99-audio-quality.conf`
- Format: `S32LE` in sink adapter args (no underscore, no quotes)
- Default format: `"F32_LE"` in pipewire.conf context.properties (underscore OK here)

## Max-Quality Config (Researched 2026-07-18)

Research source: AudioScienceReview bit-perfect guide + PipeWire official docs + soxr library docs + ALSA hardware capabilities. Cross-verified across 3+ independent sources.

### Optimal Adapter Args (alsa-sink-alc1220.conf)

Add these to the `args` block for maximum quality and stability:

```
resample.disable          = true     # bypass SRC entirely when rates match
monitor.channel-volumes   = false    # clean signal path, no per-channel volume
channelmix.upmix          = false    # prevents stereo smearing (default is TRUE!)
channelmix.mix-lfe        = false    # no subwoofer processing
channelmix.normalize      = false    # don't modify levels
node.suspend              = false    # prevent codec power-cycling
api.alsa.soft-mixer       = true     # software volume ignores hw mixer reset
priority.driver           = 9000     # wins over auto-detected sinks
priority.session          = 9000
```

**Why:** ALC1220 DAC is a 24-bit converter. F32 mantissa (24-bit) covers all 2^24 integer values exactly. S32LE transport → 24-bit DAC conversion loses no information. soxr at any quality above default is transparent (-175dB distortion), but `resample.disable=true` avoids SRC entirely when source and sink rates match. `channelmix.upmix=true` (the PipeWire default!) upmixes stereo to multi-channel unnecessarily, smearing the stereo image.

### Format Chain (final)

```
App → EE (F32P) → PW graph mixer (F32P→S32LE) → alc1220-sink (S32LE) → ALSA front:1 (S32_LE) → ALC1220 DAC
```

- ALC1220: `bits: 16 20 24 32` (integer only, no float)
- `aplay --dump-hw-params` confirms only `S16_LE S32_LE` supported (no S24_LE)
- EE always processes in F32P regardless — conversion is unavoidable

## Restoration after reinstall
1. Install pipewire, wireplumber, pipewire-pulse, easyeffects
2. Copy config files from ~/.config/pipewire/ and ~/.config/easyeffects/
3. Copy /etc/modprobe.d/snd-intel-dspcfg.conf
4. `sudo mkinitcpio -P && sudo reboot`
5. Enable and start alc1220-audio.service

## Workflow Rules (user preference)
- **Investigate vs fix:** When asked to investigate, DO NOT make changes — only gather information and report. The user will explicitly say "set" or "apply" when they want changes made.
- **No service restarts without permission:** Each PipeWire restart triggers the adapter to reopen hw:1, resetting the codec state. Use direct `amixer` commands for live volume changes.
- **Direct fixes, not deep dives:** The user wants things to work, not multi-step debugging. When stuck between isolating a problem and making it work, choose making it work.
- **Keep it brief:** Output commands and results, not explanations. The user communicates in shorthand ("s", "f", "a") and expects the same efficiency back.

## GitHub Repo (public)
Full config mirror + LLM manifest: [GitHub: sethengine/alc1220-audio-config](https://github.com/sethengine/alc1220-audio-config)
Contains exact copies of all config files, the skill doc, and `LLM.md` for LLM ingestion.

## Format Chain (as finalized in session)
```
App → EE (F32P) → [PW graph mixer: F32P→S32LE] → alc1220-sink (S32LE) → ALSA front:1 (S32_LE) → ALC1220 DAC
```
- ALC1220 DAC only accepts integer formats (`bits: 16 20 24 32`, no float)
- `audio.format = S32LE` in adapter args (SPA naming, no underscore)
- `default.audio.format = "F32_LE"` in pipewire.conf (ALSA naming, underscore OK here)
- EE processes in F32P internally regardless — conversion is unavoidable without bypassing EE entirely
- Setting both to S32 narrows the conversion but doesn't eliminate it; purely cosmetic

## GitHub Repo
All config files + full skill are mirrored at:
**https://github.com/sethengine/alc1220-audio-config**

## Related Skills
- `skill_view(name=pipewire-audio)` — general PipeWire troubleshooting, custom sinks, EasyEffects crash recovery, XM3 passive mode diagnostics
