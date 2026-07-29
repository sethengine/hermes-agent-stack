---
name: pipewire-audio
description: "PipeWire audio configuration, troubleshooting, and optimization — custom sinks, EasyEffects, codec tuning, and interference diagnostics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [pipewire, audio, easyeffects, pulseaudio, alsa, linux-desktop]
    related_skills: [alacritty-theming]
---

# PipeWire Audio Configuration

## Overview

PipeWire is the default audio server on modern Linux. This skill covers:
- Custom ALSA sink configuration for high-end codecs (ALC1220, etc.)
- EasyEffects plugin chain management and restoration
- GPU coil whine / electrical interference diagnostics
- Audio quality optimization for specific hardware

## Custom PipeWire Sinks

### Config Location

User-level configs go in `~/.config/pipewire/pipewire.conf.d/`. System-wide in `/etc/pipewire/pipewire.conf.d/`.

### Custom ALSA Sink Template

Create `~/.config/pipewire/pipewire.conf.d/alsa-sink-alc1220.conf`:

```conf
context.objects = [
    {
        factory = adapter
        args = {
            factory.name     = "api.alsa.pcm.sink"
            node.name        = "alc1220-analog-sink"
            node.description = "ALC1220 Analog (Custom Config)"
            media.class      = "Audio/Sink"

            # front:N = with hardware mixer; hw:N = raw (bypasses mixer)
            api.alsa.path    = "front:1"

            api.alsa.pcm.stream = "playback"

            # S32LE = correct native format for ALC1220 (no float support)
            # Use SPA naming: no underscore. S32_LE will crash startup.
            audio.format     = S32LE
            audio.channels   = 2
            audio.position   = "FL,FR"
            audio.rate       = 48000

            resample.quality = "soxr-vhq"
            api.alsa.period-size = 512
            api.alsa.periods = 3
            api.alsa.headroom = 0          # increase to 64-128 for underrun protection

            monitor.passthrough = false
        }
    }
]
```

### ⚠️ Critical: Format Syntax Differs By Location

**This is the most common source of PipeWire config errors.** The same format name uses different syntax depending on where it appears:

| Location | Syntax | Example |
|----------|--------|---------|
| `context.properties` (main config) | ALSA-style, with underscore, **quoted** | `default.audio.format = "S32_LE"` ✅ |
| `args` block (`adapter`, etc.) | SPA-style, **no underscore**, quotes optional | `audio.format = S32LE` ✅ (unquoted), `"S32LE"` ✅, `"S32_LE"` ❌ (breaks startup) |

The `adapter` args use **SPA format naming** (`S32LE`, `F32LE`, `S16LE`) — never the ALSA/`context.properties` form with underscore (`S32_LE`). Using `"S32_LE"` in an `args` block produces:
```
mod.adapter: usage: node.name=<string>
pw.resource: usage: node.name=<string>
pw.conf: can't create object from factory adapter: Invalid argument
```

### Key Configuration Parameters

| Parameter | Options (adapter args) | Notes |
|-----------|------------------------|-------|
| `api.alsa.path` | `hw:N` (direct), `front:N` (mixer) | `hw` bypasses mixer — needed for exclusive access; `front` enables hardware volume via ALSA mixer |
| `audio.format` | `S32LE`, `S24LE`, `S16LE`, `F32LE` | **Must match DAC capabilities.** ALC1220: integer only — `S32LE` is the correct native format. **F32/F32LE/F32P will cause PipeWire to fail to start** because the ALC1220 DAC only supports integer PCM (`bits [0x1e]: 16 20 24 32` — no float). Check capabilities with `cat /proc/asound/cardN/codec#0 \| grep -E 'rates\|bits\|formats'`. |
| `api.alsa.period-size` | 256, 512, 1024, 2048 | Lower = less latency (~5ms at 256), higher = more stability. 512 is balanced |
| `api.alsa.periods` | 2, 3, 4 | 2 = double buffer (lower latency), 3-4 = more underrun protection |
| `api.alsa.headroom` | 0-256 | Extra buffer frames. 64 prevents underruns on loaded systems (GPU spikes) |
| `resample.quality` | `soxr-vhq`, `soxr-hq`, `speex-float-N` | `soxr-vhq` is highest quality but CPU-heavy. If no resampling occurs (fixed rate), use lower |
| `default.audio.sink` | sink name | Set in main `pipewire.conf` under `context.properties` |

### Default Sink Selection

In `~/.config/pipewire/pipewire.conf`:

```conf
context.properties = {
    default.audio.sink = "alc1220-analog-sink"
    #default.audio.sink = "alsa_output.pci-0000_80_1f.3.analog-stereo"
}
```

### CRITICAL: Factory Name Must Be Quoted

In `context.objects` / `args` blocks, string values with **dots** (like `api.alsa.pcm.sink`) MUST be in quotes. Without quotes, the PipeWire config parser interprets the dots as key path separators, producing a confusing error:

```
mod.adapter: usage: node.name=<string>      ← WRONG: parser thinks node.name is missing
pw.resource: usage: node.name=<string>      ← because factory.name value was eaten by syntax error
pw.conf: can't create object from factory adapter: Invalid argument
```

**Correct:**
```conf
factory.name     = "api.alsa.pcm.sink"       # ← quoted → works
```

**Wrong (produces cryptic adapter error):**
```conf
factory.name     = api.alsa.pcm.sink          # ← unquoted → parser breaks on dots
```

This is different from the `resample.method = soxr` pitfall (where bare words are parsed as key-value separators). With dots, the parser doesn't even get to the adapter — it chokes earlier on the key-path expansion. See also the "Unquoted SPA-JSON strings" pitfall below.

### `hw:` vs `front:` — Which to Use

- **`hw:N`** — Opens the raw ALSA device. No mixer, no volume control, exclusive access. Best for custom configs that want to control everything. More susceptible to interference coupling.
- **`front:N`** — Goes through the hardware mixer. Volume is done by the codec at DAC level. Better for standard use.

### Auto-Detected Sink Conflicts

When you create a custom sink via `context.objects` with `api.alsa.path = "hw:N"`, and PipeWire's udev auto-detection also discovers the same card, **two sinks compete for the same ALSA device**. Only one can hold it open — the other goes to ERROR state with "Device or resource busy" logged in `journalctl --user -u pipewire.service`.

**Fix: use `front:N` in the custom sink instead of `hw:N`.** Both the auto-detected sink (which uses `front:N`) and the custom sink then try the same path. PipeWire's device reservation lets one hold it while the other stays SUSPENDED without errors. Then suspend the auto-detected one permanently:

```bash
pactl suspend-sink alsa_output.pci-0000_80_1f.3.analog-stereo 1
```

## Persistence Via Systemd User Services

ALSA mixer settings (headphone volume, per-channel switch states) and pactl sink selections do NOT survive a PipeWire or login restart. Create a systemd user service to restore them:

```
~/.config/systemd/user/alc1220-audio-fix.service
```

```ini
[Unit]
Description=ALC1220 Audio Fix — headphone volume, default sink, suspend auto-detected
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
ExecStartPost=/bin/sh -c '/usr/bin/pactl set-sink-mute alc1220-analog-sink 0 || true'
ExecStartPost=/bin/sh -c '/usr/bin/pactl suspend-sink alsa_output.pci-0000_80_1f.3.analog-stereo 1 || true'

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable alc1220-audio.service
```

**Design rationale:**
- `Wants=` instead of `BindsTo=` — soft dependency: if pipewire fails to start (start-limit-hit, crash loop), this service still completes its `PreExec` amixer commands at next login. `BindsTo=` would chain-fail it hard, preventing the recovery that the amixer commands are designed to provide.
- `WantedBy=default.target` instead of `WantedBy=pipewire.service` — runs once at session start regardless of pipewire lifecycle. `ExecStartPost` pactl commands swallow failures with `|| true` since pulse may not be ready yet.
- `ExecStartPre=/usr/bin/sleep 5` — critical: alsa hardware needs enumeration, pipewire socket needs to be ready before amixer/pactl connect.

## PipeWire Quantum / Buffer Tuning

### What It Controls

The PipeWire `quantum` is the number of audio frames per processing cycle. It directly impacts latency vs stability:

| Quantum | @48kHz | Latency | Stability |
|---------|--------|---------|-----------|
| 256 | 5.3ms | Lowest | Prone to xruns with heavy processing |
| 512 | 10.7ms | Low | Balanced for light EE chains (≤5 plugins) |
| 1024 | 21.3ms | Medium | Stable for heavy EE chains (DeepFilterNet, 11+ plugins) |
| 2048 | 42.7ms | High | Very stable — use on very loaded systems |

### Where to Set It

There are **three layers** that can set these — config files override each other in alphabetical order:

1. **Main config**: `~/.config/pipewire/pipewire.conf` — top-level defaults
2. **Override files**: `~/.config/pipewire/pipewire.conf.d/*.conf` — loaded after main, alphabetical, can override
3. **Runtime metadata**: `pw-metadata -n settings` — dynamic, set by WirePlumber for adaptive behavior

Always check which file actually takes effect by looking at `pw-metadata -n settings 2>&1 | grep clock` and the alphabetically-last `.d/*.conf` file. Common pitfall: setting quantum=1024 in `pipewire.conf` but a later-loaded `99-audio-quality.conf` overrides it back to 512.

### Configuration

In the relevant config file (main or overrides-dropin):

```conf
context.properties = {
    default.clock.rate          = 48000
    default.clock.allowed-rates = [ 48000 ]
    default.clock.quantum       = 1024      # frames per cycle
    default.clock.min-quantum   = 512       # minimum (won't go below)
    default.clock.max-quantum   = 8192      # maximum if adaptive
    #default.clock.quantum-limit = 8192     # uncomment to cap
}
```

### When to Increase Quantum (→ heavier processing)

- User reports **periodic crackling/pops every 1-5 minutes** — classic underrun symptom: the quantum is too small for the processing chain to keep up. Increasing from 256→1024 gives the DSP pipeline 4× more scheduling slack.
- EasyEffects chain has **10+ plugins** including neural network filters (DeepFilterNet, Noise models)
- Chain includes CPU-heavy plugins: **soxr-vhq resampling + DeepFilterNet + Crystalizer** simultaneously
- System is under periodic background load (compilation, backups, browser with many tabs)
- PipeWire shows `(Start error: Device or resource busy)` or `xrun` in journal

### When to Decrease Quantum (→ lower latency)

- User is a musician using PipeWire for **live monitoring / instrument input**
- User reports **audible delay** between action and sound (e.g., clicking drum pad, guitar amp sim)
- Light processing chain (≤3 plugins, no neural nets)
- Real-time audio workstation (REAPER, Bitwig, Ardour)

### Debugging

```bash
# Current effective quantum
pw-metadata -n settings 2>&1 | grep clock.quantum

# Check both config files for quantum values — the later file wins
grep -rn "clock.quantum\|clock.min-quantum\|clock.max-quantum" \
  ~/.config/pipewire/pipewire.conf \
  ~/.config/pipewire/pipewire.conf.d/ 2>/dev/null

# Check if adaptive is active (force-quantum=0 = adaptive)
pw-metadata -n settings 2>&1 | grep force-quantum

# Monitor xruns (underruns) in real time — run during playback
pw-top 2>&1

# Journal xrun events after the fact
journalctl --user -u pipewire.service --since "5 min ago" | grep -iE "xrun|underrun|error"
```

### Pitfall: Override File Alphabetical Order

Files in `pipewire.conf.d/` are loaded **alphabetically**. A file named `99-foo.conf` overrides `10-bar.conf`, which overrides the main `pipewire.conf`. If you set quantum=1024 in `pipewire.conf` but `99-audio-quality.conf` sets quantum=512, the effective value is 512. Always check the last-loaded file:

```bash
ls ~/.config/pipewire/pipewire.conf.d/ | sort
grep -rn "quantum" ~/.config/pipewire/pipewire.conf.d/ | sort
```

## EasyEffects Configuration

### Architecture

Audio flows: **App → easyeffects_sink → EE plugins chain → physical sink**

### Plugin Chain Storage

- **Main config**: `~/.config/easyeffects/db/easyeffectsrc`
- **Per-plugin settings**: `~/.config/easyeffects/db/<plugin>rc` — INI format with `[soe][PluginName#N]` sections
- **Output presets**: `~/.config/easyeffects/output/*.json`
- **Input presets**: `~/.config/easyeffects/input/*.json`

### Plugin Chain Format

In `easyeffectsrc` under `[StreamOutputs]`:

```ini
[StreamOutputs]
outputDevice=alc1220-analog-sink
plugins=bass_enhancer#0,bass_loudness#0,equalizer#0,equalizer#1,pitch#0,exciter#0,crystalizer#0,equalizer#2,equalizer#3,limiter#0,deepfilternet#0,stereo_tools#0
```

### ⚠️ Reading Plugin Bypass States

The `plugins=` line in `easyeffectsrc` lists **all configured plugins** — both active and bypassed. To determine the **actual effective chain**, check each plugin's per-plugin `rc` file for the `bypass` flag under its `[soe][PluginName#N]` section:

The `rc` files use INI-format sections (not JSON). The plugin name from the `plugins=` list maps to a section in `<plugin>rc`:
- `bass_enhancer#0` → `[soe][BassEnhancer#0]` in `bassEnhancerrc`
- `equalizer#0` → `[soe][Equalizer#0]` in `equalizerrc`
- `limiter#0` → `[soe][Limiter#0]` in `limiterrc`

**Key rule**: if the section has no `bypass` key at all, the plugin is **active**. Only plugins with `bypass=true` explicitly set are skipped.

```bash
# Quick dump of all plugin bypass states
for f in ~/.config/easyeffects/db/*rc; do
  name=$(basename "$f")
  echo "=== $name ==="
  grep -E "^\[soe\]|^bypass=" "$f"
  echo
done
```

**Output interpretation:**
```ini
# ACTIVE — no bypass key present
[soe][BassEnhancer#0]
amount=6.06

# BYPASSED — bypass=true present
[soe][Exciter#0]
bypass=true
amount=3.42
```

**Common pitfall**: Do NOT assume all plugins on the `plugins=` line are running. On a typical user-configured chain, 50-75% may be bypassed. The bypassed plugins still appear in the list because EE preserves the full chain layout; they just pass audio through unmodified. Always verify by checking the actual `bypass` flags before describing which processing is active.

### Adding an EQ to the Chain

1. Add to the `plugins=` list in `easyeffectsrc`
2. Add EQ band config to the `equalizerrc` file:

```ini
[soe][Equalizer#3]
numBands=15

[soe][Equalizer#3#left]
band0Frequency=250
band0Gain=3.5
band0Mode=6
band0Q=0.8
band0Type=1
# ... more bands ...
band5Type=0  # unused bands = type 0

[soe][Equalizer#3#right]
# same as left
```

### Band Types

| Type | Meaning |
|------|---------|
| 0 | Off |
| 1 | Parametric |
| 2 | Low Shelf |
| 3 | High Shelf |
| 4 | Low Pass |
| 5 | High Pass |
| 6 | Notch |
| 7 | Band Pass |

### Crash Recovery (PipeWire restart during EE playback)

When PipeWire restarts or sinks change while EasyEffects is running, EE can SIGABRT (signal 6) — the symptom is a coredump showing `lsp-plugins-lv2.so` + `libQt6Core.so QDebug destructor` + `abort()` in the main thread. This is a chain failure, not a specific plugin bug: EE's PipeWire client gets disconnected, the connection error triggers a Qt assertion in QDebug logging, which calls abort.

**Recovery sequence:**

```bash
# 1. Identify the sink EE was using (may have been a custom sink that vanished)
grep outputDevice ~/.config/easyeffects/db/easyeffectsrc

# 2. Verify the sink still exists
pactl list short sinks | grep "$(grep outputDevice ~/.config/easyeffects/db/easyeffectsrc | cut -d= -f2)"

# 3. Check EE config didn't truncate during crash (common)
grep 'plugins=' ~/.config/easyeffects/db/easyeffectsrc

# 4. Verify plugin chain is complete (count the plugins match what user expects)
grep 'plugins=' ~/.config/easyeffects/db/easyeffectsrc | wc -w

# 5. Restart EE
systemctl --user restart app-com.github.wwmm.easyeffects@*.service

# Or manually:
killall easyeffects 2>/dev/null
sleep 1
easyeffects --gapplication-service &
```

**If the plugin chain truncated** (some plugins missing in `plugins=` line):
- Restore from backup: `cp ~/easyeffects-backup-*/easyeffectsrc ~/.config/easyeffects/db/easyeffectsrc`
- Or re-add plugins via the EE GUI and let EE save its own config

**Prevention:** Use `Wants=` (not `BindsTo=`) in the persistence service so PipeWire restarts don't chain-fail the audio fix service. See "Persistence Via Systemd User Services" above.

### Restoring After Crash/Restart

When PipeWire or EasyEffects restarts, the in-memory plugin state can reset:

1. Check `~/.config/easyeffects/db/easyeffectsrc` for `plugins=` line
2. If truncated (e.g., only `equalizer#0`), restore from backup
3. Restart EasyEffects: `easyeffects -q` then `easyeffects --gapplication-service` (background)
4. Verify sinks appear: `pactl list short sinks | grep easy`

### Backup All Audio State

```bash
cp -r ~/.config/easyeffects/ ~/easyeffects-backup-$(date +%Y%m%d)
cp -r ~/.config/pipewire/ ~/pipewire-backup-$(date +%Y%m%d)
```

## GPU Coil Whine → Analog Audio Interference

### Symptoms
- Electric buzzing/humming in headphones when GPU is under load (games, rendering)
- Sound changes with GPU power draw
- Both case noise (coil whine) AND headphones buzzing

### Root Cause
GPU VRM inductors switching at high frequency create electrical noise that couples through the motherboard ground plane into the analog audio codec (ALC1220, etc.).

### Diagnostic Steps

1. **Confirm GPU is the source**:
   ```bash
   nvidia-smi --query-gpu=power.draw,clocks.current.graphics --format=csv
   ```
   Run a GPU load (game, stress test) and listen for the buzz.

2. **Check active audio device**:
   ```bash
   pactl list short sinks
   cat /proc/asound/cards
   ```

### Mitigations (in order of effectiveness)

| Fix | Cost | Effectiveness |
|-----|------|--------------|
| **USB DAC** (Apple USB-C to 3.5mm dongle) | ~$9-20 | 99% — completely bypasses motherboard analog circuit |
| **Disable NVIDIA HDMI audio** | Free | Sometimes helps — unbind PCI device. User preference matters — some strongly prefer not to. |
| **Rear vs front panel** | Free | One path may be noisier than the other. Rear line-out vs front headphone jack use different DAC nodes |
| **GPU undervolt** | Free | Reduces VRM switching noise at source |
| **PipeWire period-size increase** | Free | Larger buffers = fewer interrupts = less noise coupling |

### What NOT to Do
- Do NOT mess with PipeWire default sink without confirming the original sink first
- Do NOT restart PipeWire without checking the EasyEffects state file will survive
- Do NOT blacklist NVIDIA audio driver without explicit user approval

## Sony WH-1000XM3

### Passive Mode (Powered Off via Aux) — "Tin Can" Sound Fix

The XM3's drivers are **designed to rely on internal DSP**. When used via aux cable with the headphones **powered off** (passive mode), the raw driver frequency response is notoriously bad:
- **Sub-bass drops off a cliff** below ~100Hz → no body/warmth
- **Lower-mids are recessed** (~200-400Hz) → hollow "tin can" sound
- **Upper treble has raw peaks** (~8kHz) → harsh/ear-dominant

**First thing to check when user reports tinny/thin/hollow sound via aux: is the headphone powered on?** Powering them on (even with NC/Ambient off) engages the internal DSP which corrects the frequency response. This fixes 99% of "tin can" complaints.

See also: `skill_view(name='pipewire-audio', file_path='references/sony-wh1000xm3-passive-mode.md')` for full diagnostic steps, XM3-specific EQ curve, and verification commands.

### Active Mode EQ Tuning (Powered On, Wired or Bluetooth)

The XM3 has known residual frequency response issues even with DSP active:
- **Recessed lower-mids (~200-400Hz)** → thin vocals
- **Sharp peak (~8kHz)** → harsh treble

### Recommended EQ Curve (for EasyEffects or PEQ app)

| Freq | Gain | Type | Purpose |
|------|------|------|---------|
| 80Hz | +2dB | Low Shelf | Sub-bass weight |
| 250Hz | +3.5dB | Parametric | Fill thin lower-mids (fixes "tin can") |
| 500Hz | +1.5dB | Parametric | Vocal body smooth transition |
| 2kHz | -0.5dB | Parametric | Calm upper-mid presence |
| 6kHz | -1.5dB | Parametric | Pre-smooth before treble cut |
| 8.2kHz | -3.0dB | Parametric (Q=3) | Tame sharp 8kHz peak |
| 14kHz | -1.0dB | High Shelf | Smooth top-end air |

## Intel HDA/SOF Driver Binding Diagnostics

Modern Intel platforms (Z690, Z790, Z890 with ACE audio controller, Meteor Lake / Arrow Lake) require the **SOF (Sound Open Firmware)** driver stack. The legacy `snd_hda_intel` driver may fail to bind, leaving the motherboard codec invisible to ALSA/PipeWire.

### Symptoms

- Motherboard analog audio doesn't appear in `pactl list short sinks` or `aplay -l`
- GPU HDMI audio works fine
- `cat /proc/asound/cards` shows only the NVIDIA/AMD card
- `lspci | grep Audio` shows the Intel audio device (e.g., `80:1f.3 Audio device: Intel Corporation 800 Series ACE`)
- `journalctl -k | grep -E "hda|sof"` shows one of:
  - `couldn't bind with audio component` (snd_hda_intel attempted, failed)
  - `the DSP is not enabled on this platform, aborting probe` (SOF attempted, failed)

### Two-Failure Mode (Z890 ACE / Arrow Lake)

On Gigabyte Z890 AERO G and similar boards, **both drivers fail** — not just one:

| Driver | Error | Why |
|--------|-------|-----|
| `snd_hda_intel` | `couldn't bind with audio component` | Needs i915/Xe display driver's audio component — fails on systems with **no Intel iGPU** (KF-series CPUs, dGPU-only) |
| `sof-audio-pci-intel-mtl` | `DSP is not enabled on this platform, aborting probe` | PCI class is `0x040300` (generic), SOF only accepts `0x040100` (HDA) or `0x040380` (DSP-enabled). BIOS must set the correct class code |

### Root Cause Hierarchy

1. **Driver race**: `snd_hda_intel` matches PCI ID `8086:7f50` and binds first, but can't drive the ACE controller → `deferred probe pending: couldn't bind with audio component`
2. **SOF class check**: If `snd_hda_intel` unbinds, SOF tries next but checks `pci->class != 0x040100 && pci->class != 0x040380` — the ACE reports `0x040300` because the BIOS hasn't configured it for DSP mode → `DSP is not enabled on this platform`
3. **No iGPU = no audio component**: `snd_hda_intel`'s "bind with audio component" requires i915/Xe. On dGPU-only builds (no Intel iGPU), this can never succeed.

### Diagnostic Flow

```bash
# Identify audio PCI devices
lspci | grep -i "audio\\|HDMI\\|hda"

# Check visible ALSA cards
cat /proc/asound/cards

# Check which driver is bound
ls -la /sys/bus/pci/devices/0000:80:1f.3/driver/ 2>/dev/null || echo "unbound"

# Check kernel logs for driver failures
journalctl -k --no-pager | grep -iE "hda.*intel.*1f.3|audio.*component|deferred probe|sof.*1f.3|DSP.*not enabled"

# Check PCI class code (critical for SOF acceptance)
cat /sys/bus/pci/devices/0000:80:1f.3/class   # 0x040300 = generic (bad), 0x040380 = DSP (good)

# Check DSP driver config
cat /sys/module/snd_intel_dspcfg/parameters/dsp_driver
# 0=auto, 1=legacy HDA, 2=SST, 3=SOF, 4=AVS

# Check what drivers match the device
lspci -v -s 80:1f.3 | grep "Kernel modules"

# List PipeWire sinks
pactl list short sinks

# Check SOF firmware availability
ls /lib/firmware/intel/sof-ipc4/mtl/
```

### When It Works (typical fix — SOF with `dsp_driver=3`)

Works when the platform has an Intel iGPU AND the BIOS sets the correct PCI class:

```bash
echo "options snd-intel-dspcfg dsp_driver=3" | sudo tee /etc/modprobe.d/snd-intel-dspcfg.conf
```

`dsp_driver` values: `0`=auto (may pick wrong), `1`=legacy HDA, `2`=SST, **`3`=SOF (correct for ACE)**, `4`=AVS (alternative SOC driver).

### When `dsp_driver=3` Still Fails ("DSP not enabled")

This is a **BIOS/firmware limitation**, not a driver config issue. The ACE controller reports PCI class `0x040300` (generic multimedia audio) which the SOF kernel driver rejects.

**Fix options in priority order:**

1. **Try `dsp_driver=1` (force legacy HDA)** — On some boards (Gigabyte Z890 AERO G confirmed), forcing the legacy `snd_hda_intel` driver via `dsp_driver=1` actually works where SOF (`dsp_driver=3`) fails. This is counterintuitive because the ACE controller is a SOF-era device, but the legacy driver can drive it when SOF's DSP check blocks. Add to `/etc/modprobe.d/snd-intel-dspcfg.conf`:
   ```
   options snd-intel-dspcfg dsp_driver=1
   ```
   Then rebuild initramfs and reboot:
   ```bash
   sudo mkinitcpio -P   # Arch/Manjaro
   # or
   sudo update-initramfs -u  # Debian/Ubuntu
   sudo reboot
   ```

2. **BIOS setting** — Look for a DSP-specific enable on Gigabyte boards:
   - *Peripherals → Audio DSP → Enabled*
   - *Settings → Miscellaneous → Onboard Audio Configuration*
   - The correct PCI class after BIOS fix should be `0x040380`
   
3. **Live workaround (no reboot)** — If you can't find the BIOS setting, you need to either:
   - Try `dsp_driver=4` (AVS driver) — may work on some platforms
   - Or patch the SOF kernel module's PCI class check in `sound/soc/sof/intel/hda.c`
   
4. **Kernel downgrade** — If it worked on an older kernel, boot the LTS/older kernel via GRUB

### Live Rebind (no reboot)

After setting the dsp_driver config and reboot, or if the right driver is already loaded:

```bash
# Check current driver state
cat /sys/bus/pci/devices/0000:80:1f.3/driver 2>/dev/null || echo "unbound"

# Unbind from wrong driver
echo 0000:80:1f.3 | sudo tee /sys/bus/pci/drivers/snd_hda_intel/unbind 2>/dev/null

# If SOF module name varies (check actual name in sysfs):
ls /sys/bus/pci/drivers/ | grep sof

# Bind to SOF
echo 0000:80:1f.3 | sudo tee /sys/bus/pci/drivers/sof-audio-pci-intel-mtl/bind 2>/dev/null
# Or reload modules directly:
sudo modprobe -r snd_hda_intel
sudo modprobe snd_sof_pci_intel_mtl
```

### Verify

```bash
cat /proc/asound/cards       # new Intel card should appear
aplay -l                     # should list analog device
pactl list short sinks       # PipeWire analog sink visible
speaker-test -c 2 -l 1 -D hw:1   # test playback (adjust hw:N as needed)
```

### Pitfalls

- **`hw:N` paths change after rebind** — Intel card index may shift. Update custom PipeWire sink `api.alsa.path` accordingly (or use card-name-based addressing like `"alsa_output.pci-0000_00_1f.3.analog-stereo"` instead of `hw:1`).
- **NVIDIA HDMI is on separate PCI device** (`02:00.1`) — `dsp_driver=3` only affects the Intel-integrated controller; NVIDIA continues using `snd_hda_intel`.
- **SOF firmware needed** — Check `/lib/firmware/intel/sof-ipc4/` for platform firmware. Install `sof-firmware` package if missing (`pacman -S sof-firmware`).
- **Existing `snd_hda_intel` options in modprobe.d** — Global options like `snoop=1`, `position_fix=1` apply to ALL `snd_hda_intel` devices. They can cause the ACE controller to fail binding. If your config has these, try removing them or using per-device `enable=1,0` syntax.
- **No iGPU on system** — If the CPU lacks integrated graphics (KF/F series), `snd_hda_intel` will **always** fail with "couldn't bind with audio component" because the i915/Xe display driver's audio component doesn't exist. SOF is the only path — but requires the BIOS DSP setting.
- **`dsp_driver` is often READ-ONLY at runtime** — Check with `ls -la /sys/module/snd_intel_dspcfg/parameters/dsp_driver`. If `-r--r--r--` (common on Arch/Manjaro kernels), it **cannot** be changed live — only set at module load time via modprobe.d or kernel cmdline. This means fixing a bad `dsp_driver` config requires a reboot (or `modprobe -r` chain to unload/reload the entire audio stack). Do NOT advise `echo N > .../parameters/dsp_driver` without first verifying it's writable.
- **Kernel upgrade 6.18 → 7.0 triggered regression** — The kernel 7.0 series changed driver binding behavior on some Z890 boards. If audio worked on 6.18 but broke on 7.0, the issue may be a kernel regression.
- **`echo ... > .../bind` fails with \"No such device\" after unbind** — If `dsp_driver` is baked into the kernel (read-only param), the unbind removes the device from the wrong driver but the correct driver's `bind` file may reject it because the snd_intel_dspcfg redirect isn't re-evaluated. The device enters an unbound state that only a reboot or full `modprobe -r` chain can fix.
- **EasyEffects/EQ crashes when the audio sink disappears** — If the default audio sink vanishes (driver rebind, PipeWire restart during config change), EasyEffects will SIGABRT (signal 6) with a coredump. Restoring the sink and restarting EE (`easyeffects -q && easyeffects --gapplication-service &`) fixes it, but verify the `easyeffectsrc` plugin chain didn't truncate during the crash.
- **`pkexec` for sysfs writes** — If `sudo` requires a password in non-interactive terminals, try `pkexec` or add SUDO_PASSWORD to `~/.hermes/.env`. Note that `pkexec` may show a GUI dialog that times out.

- **ALC1220 right channel mute / ALSA simple mixer lies** — On ALC1220 (and possibly other codecs), the `amixer` simple mixer control `Headphone` may report setting values correctly while the underlying hardware register (`numid=3 Headphone Playback Volume`) remains at 0. The simple mixer abstraction and the hardware control are different objects — the former shows phantom success. Always verify with `amixer cget numid=3` to read the real register, and set with `amixer cset numid=3 87,87` + `amixer cset numid=4 on,on` instead of relying on `amixer set Headphone 87 unmute`. These settings reset to 0 on PipeWire restart — see "Persistence Via Systemd User Services" above to make them stick.
  ```bash
  # Verify actual hardware state (not simple mixer abstraction)
  amixer -c1 cget numid=3       # Headphone Playback Volume
  amixer -c1 cget numid=4       # Headphone Playback Switch
  # Set directly (this actually works)
  amixer -c1 cset numid=3 87,87
  amixer -c1 cset numid=4 on,on
  ```
  The simple mixer name "Headphone" and the control numid=3 "Headphone Playback Volume" may not be the same control under the hood — the simple mixer abstraction can show phantom success while the physical register stays at 0. Use `numid=` for guaranteed writes.

- **PipeWire crash recovery after EasyEffects SIGABRT** — EasyEffects crashes (e.g., SIGABRT from `lsp-plugins-lv2.so` when the audio sink disappears during PipeWire restart) can take down the entire PipeWire stack and leave stale socket files. Recovery sequence:
  ```bash
  # 1. Reset systemd rate limits
  systemctl --user reset-failed pipewire pipewire-pulse wireplumber
  # 2. Remove stale sockets (block restart if left over from crash)
  rm -f /run/user/$UID/pipewire-0 /run/user/$UID/pipewire-0-manager
  # 3. Start services in dependency order
  systemctl --user start pipewire.socket
  systemctl --user start pipewire.service
  systemctl --user start pipewire-pulse.socket
  systemctl --user start pipewire-pulse.service
  systemctl --user start wireplumber
  # 4. Verify sinks restored
  pactl list short sinks
  pactl info | grep 'Default Sink'
  # 5. Check EasyEffects config didn't truncate during crash
  grep 'plugins=' ~/.config/easyeffects/db/easyeffectsrc
  ```

- **Stale socket files block PipeWire restart** — After a hard crash (SIGKILL), `/run/user/$UID/pipewire-0` and `pipewire-0-manager` may be **unlinked from the filesystem** while systemd's socket unit still holds the file descriptor. The files disappear from `ls -la` but still appear in `/proc/net/unix`. Trying `rm -f` has no effect (already unlinked), and `systemctl restart` fails because the old fd is stale. **Fix:** stop the socket unit explicitly FIRST (which closes the stale fd), then start fresh:
  ```bash
  systemctl --user stop pipewire.socket        # ← MUST do this before rm
  systemctl --user stop pipewire wireplumber pipewire-pulse 2>/dev/null
  rm -f /run/user/$UID/pipewire-0 /run/user/$UID/pipewire-0-manager
  systemctl --user reset-failed pipewire pipewire-pulse wireplumber
  systemctl --user start pipewire.socket
  systemctl --user start pipewire.service
  systemctl --user start pipewire-pulse.socket
  systemctl --user start pipewire-pulse.service
  systemctl --user start wireplumber
  pactl info | head -3              # verify connection
  ```

### Workflow Preference: Fix First, Don't Isolate

When the user asks you to fix a non-working audio stack, **do not isolate configs one by one before fixing**. The priority is restoring audio as fast as possible. Follow this order:

1. **Restore the stack** — clean sockets, restart services, reset failed units. Get audio playing on any working sink first.
2. **Verify the hardware** — `cat /proc/asound/cards`, `aplay -l`, `cat /sys/module/snd_intel_dspcfg/parameters/dsp_driver`
3. **Fix the root cause** — modprobe.d, format syntax, quantum, etc.
4. **Apply all fixes at once** — then present the full diff to the user, not step-by-step progress
5. **Validate** — ask the user to test, collect any remaining symptom, then iterate

Only isolate configs as a last resort when the fix isn't obvious. Most PipeWire issues have known patterns — use them directly rather than binary-searching configs.

```bash
# List sinks and active state
pactl list short sinks

# Check default sink
pactl info | grep 'Default Sink'

# Diagnose hardware vs PipeWire: test ALSA directly (bypasses PipeWire entirely)
# If this works but PipeWire doesn't, the issue is PipeWire config, not hardware
# Adjust hw:N,M to your card:device from 'aplay -l'
speaker-test -c2 -D plughw:1,0 --test=wav -l1

# Switch default (temporary, survives PipeWire restart if in config)
pactl set-default-sink <name>

# Move running apps to another sink
for input in $(pactl list short sink-inputs | awk '{print $1}'); do
  pactl move-sink-input "$input" <sink-name>
done

# Restart EasyEffects
easyeffects -q && easyeffects --gapplication-service &

# Check ALSA card capabilities
cat /proc/asound/card*/codec#0 | grep -E 'rates|bits|formats'

# Check ALC1220 codec details
cat /proc/asound/card1/codec#0
```

## Pitfalls

- **PipeWire restart kills EasyEffects in-memory state** — Always check `easyeffectsrc` after restarting PipeWire. The plugin chain may reset to default.
- **`hw:N` paths change after driver rebind** — Unbinding/re-binding the NVIDIA HDMI audio can change ALSA card indices. Use card names instead of numbers when possible.
- **SATA controller disabled in BIOS = no hotplug** — If the SATA controller doesn't appear in lspci, it's BIOS-disabled and cannot be hot-added. Need reboot + BIOS change.
- **EasyEffects saves state on exit** — Killing EasyEffects (SIGKILL) is safer than graceful shutdown if you want to preserve a known-good config file. Graceful shutdown overwrites config with current (possibly broken) state.

- **Misreading the EE plugin chain — assuming all listed plugins are active** — The `plugins=` line in `~/.config/easyeffects/db/easyeffectsrc` lists every plugin that was ever added to the chain, including those the user bypassed. Presenting all 12 plugins as "the processing chain" without checking bypass flags is misleading. Always cross-reference each plugin's `rc` file for `bypass=true` before describing active processing. About 50-75% of plugins may be bypassed on a curated chain.

- **Unquoted SPA-JSON strings cause &quot;Expected object key&quot; syntax error** — In PipeWire config files, string values in `context.objects` / `args` blocks MUST be quoted. Bare words like `resample.method = soxr` are parsed as key-value separators, not values. Fix: `resample.quality = 10` (quality 10 = soxr-vhq without needing method=soxr). The `resample.method` key uses string values (`&quot;speex-float-1&quot;`, `&quot;soxr&quot;`) and `resample.quality` uses integer values — only one is needed because quality 10 already selects soxr-vhq.

  **Critical caveat: dots in factory names.** `factory.name = api.alsa.pcm.sink` (unquoted with dots) produces a **different, more cryptic error** than bare words — not a syntax error, but the adapter factory printing its usage:
  ```
  mod.adapter: usage: node.name=<string>
  pw.resource: usage: node.name=<string>
  pw.conf: can't create object from factory adapter: Invalid argument
  ```
  The parser interprets `api.alsa.pcm.sink` as key-path expansion (api/alsa/pcm/sink) and never reaches node.name. Always quote factory names with dots.

  | Pattern | Symptom | Fix |
  |---------|---------|-----|
  | `resample.method = soxr` (bare word) | Syntax error | Quote or use quality=10 |
  | `factory.name = api.alsa.pcm.sink` (dots, no quotes) | Cryptic adapter usage | Wrap in quotes: `&quot;api.alsa.pcm.sink&quot;` |

- **`audio.format` in adapter args: ALC1220 DAC only accepts integer formats** — Check the codec's PCM capabilities before setting `audio.format` in a custom sink. The ALC1220 DAC reports `bits [0x1e]: 16 20 24 32` (all integer). Using `F32LE` or `F32_LE` here will crash PipeWire on startup because the ALSA `front:N` device can't negotiate float with a hardware DAC that doesn't support it, and the adapter factory fails with `mod.adapter: usage: node.name=<string>` (same misleading error as unquoted factory names). Always use `S32LE` (or `S24LE`, `S16LE`) for this codec. Verify hardware capabilities with `cat /proc/asound/cardN/codec#0 | grep -E 'rates|bits|formats'`.

- **`default.audio.format` vs `audio.format` — "S32 everywhere" doesn't skip the conversion** — Setting both the global default and the sink format to S32_LE/S32LE is syntactically valid and works. However, it does NOT eliminate the F32P→S32LE conversion because EasyEffects processes internally in float (F32P) regardless of the sink format or global default. EE's processing chain always outputs float; the conversion to S32LE happens at the EE→sink link boundary in PipeWire's graph mixer. Setting both to S32LE just means the global default matches the sink format — a cosmetic simplification, not a performance gain. The real conversion is unavoidable unless EE itself is bypassed entirely. Either `F32_LE` or `S32_LE` works for the global default — pick whichever reads cleaner.

- **`default.audio.format` in `context.properties` vs `audio.format` in adapter args are different things** — The main config's `default.audio.format = "F32_LE"` sets the global default for source nodes that don't specify their own format. It does NOT affect the custom sink's format. Even if the global default is F32_LE, the alc1220 sink overrides it with `audio.format = S32LE`. EasyEffects' internal processing uses F32P (float planar) regardless — the conversion from F32P → S32LE happens at the PipeWire graph link boundary, not at the ALSA level. This is normal and handled by PipeWire's graph mixer efficiently. Do not confuse the two settings.

- **EasyEffects SIGABRT from corrupted INI-as-JSON preset** — EE stores presets as JSON in `~/.local/share/easyeffects/output/*.json`. If a file has a `.json` extension but contains INI-format data, EE throws a parse error and crashes. Symptom: `presets_manager.cpp parse error at line 1, column 2: invalid literal`. Fix: delete the corrupted file and verify with `head -c1 <file> | grep -q "{"`.

## Related Skills

- `skill_view(name=alc1220-audio-config)` — Gigabyte Z890 AERO G specific: error transcripts, LLM context, full config file mirror on GitHub
