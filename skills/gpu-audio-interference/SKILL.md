---
name: gpu-audio-interference
description: "Diagnose and fix GPU electrical noise (coil whine) bleeding into analog audio on Linux — NVIDIA GPU VRM switching noise coupling through motherboard ground plane into onboard audio codecs (Realtek ALCxxx, etc.). Covers runtime mitigation, permanent fixes, and long-term hardware solutions."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [linux, gpu, nvidia, audio, coil-whine, troubleshooting, hardware]
    related_skills: [linux-desktop-performance-audit, systematic-debugging]
---

# GPU Audio Interference (Coil Whine → Analog Audio)

## When to Use

Trigger when the user reports:
- Buzzing, whining, or static noise **through headphones/speakers** that correlates with GPU load (games, stress tests, GPU compute)
- "Electric buzzing" from the PC case that also appears in the audio output
- Noise starts when launching GPU-intensive apps and subsides when idle
- Audio is connected via motherboard's **analog audio jack** (rear line-out or front panel)
- The onboard audio codec is a Realtek ALCxxx or similar analog codec

## Root Cause

High-power NVIDIA (and some AMD) GPUs generate significant coil whine from their VRM inductors under load. This high-frequency switching noise:

1. **Couples through the motherboard's ground plane** — the GPU and audio codec share a common ground; VRM switching creates ground-plane ripple that the audio codec reads as signal
2. **Bleeds into the analog audio path** — the Realtek ALC1220 (and similar) onboard codecs perform DAC conversion on the same PCB, so the noise is amplified along with the audio signal
3. **Changes with GPU power draw** — the pitch/frequency of the noise shifts as GPU clock and voltage adjust

The NVIDIA HDA audio device (HDMI/DP audio controller on the GPU) being active on the PCI bus sometimes contributes additional interference, even when unused.

## Diagnostic Flow

### Step 1: Confirm the pattern and check recent changes

Before deep-diving, check if anything changed recently on the system:

```bash
# Check PipeWire config modification times — recent edits may have changed
# the audio routing or codec path
stat ~/.config/pipewire/pipewire.conf ~/.config/pipewire/pipewire.conf.d/*.conf 2>/dev/null | grep -E 'File:|Modify:'

# Check if PipeWire was recently updated
grep -i pipewire /var/log/pacman.log 2>/dev/null | tail -5
```

Then confirm the pattern:

```
# Check if noise correlates with GPU load
nvidia-smi --query-gpu=name,power.draw,clocks.current.graphics --format=csv,noheader

# Under load, you'll see power draw spike (95W+ for RTX 5060 Ti, 200W+ for higher-tier cards)
# Under idle, power drops significantly
```

Listen for: noise that appears during game launches, 3D rendering, or any GPU-intensive task, and subsides when the GPU returns to idle.

### Step 2: Identify audio path

```
# List ALSA sound cards
cat /proc/asound/cards

# Identify active audio sink
pactl list short sinks

# Identify active audio port
pactl list sinks | grep -E "Active Port|analog-output"
```

**Key findings:**
- **`analog-output-lineout`** = rear panel (green jack on motherboard I/O)
- **`analog-output-headphones`** = front panel (case headphone jack)
- If the active sink is an **NVIDIA HDMI/DP output**, the user is not using analog audio — the problem is different (HDMI ground loop or monitor internal speakers)
- If the active port says "not available" for headphones but shows lineout, check whether the front panel is physically connected to the motherboard's HD_AUDIO header

### Step 3: Check for custom PipeWire sink configurations

Custom PipeWire configs in `~/.config/pipewire/pipewire.conf.d/` or `/etc/pipewire/pipewire.conf.d/` can create **additional ALSA sinks** that bypass the normal hardware mixer abstraction:

```bash
# List custom PipeWire config files
ls -la ~/.config/pipewire/pipewire.conf.d/ 2>/dev/null
ls -la /etc/pipewire/pipewire.conf.d/ 2>/dev/null

# Check file modification times to see if anything changed recently
stat ~/.config/pipewire/pipewire.conf.d/*.conf 2>/dev/null | grep -E 'File:|Modify:'

# Read each custom sink config
cat ~/.config/pipewire/pipewire.conf.d/alsa-sink-*.conf 2>/dev/null
```

**What to look for:**
- Custom sinks using **`api.alsa.path = "hw:1"`** instead of `"front:1"` or the default — raw `hw:X` access bypasses the ALSA mixer layer, changing how the codec's DAC interacts with the motherboard electrically
- The `default.audio.sink` override in `~/.config/pipewire/pipewire.conf` — this forces all audio through a specific sink name:
  ```conf
  default.audio.sink = "alc1220-analog-sink"  # forces routing to custom sink
  ```
- Multiple custom sinks for the same hardware (e.g. both `alc1220-analog-sink` and the standard `alsa_output.pci-XXXX.analog-stereo`) — the user may not realize which one is active
- A template for creating (or comparing against) a custom ALSA sink is available at `references/custom-alsa-sink-template.conf` in this skill's directory

**Diagnostic:** Compare noise between the standard WirePlumber-managed sink and the custom sink by switching at runtime:

```bash
# Switch to standard sink (WirePlumber-managed, uses ALSA mixer layer)
pactl set-default-sink alsa_output.pci-0000_80_1f.3.analog-stereo
pactl move-sink-input <INPUT_ID> alsa_output.pci-0000_80_1f.3.analog-stereo

# Switch back to custom sink
pactl set-default-sink alc1220-analog-sink
pactl move-sink-input <INPUT_ID> alc1220-analog-sink
```

If noise changes between the two, the custom sink config is a contributing factor. The standard sink goes through `front:X` (ALSA mixer abstraction) while `hw:X` hits the DAC directly.

**Pitfall:** Custom sinks created via `pipewire.conf.d/` override the auto-detected profile the user may have configured in their desktop environment's audio settings. The audio may work through a completely different codec path than what `pavucontrol` or the system tray shows.

### Step 3b: Check EasyEffects / PipeWire processing pipeline

If the user has **EasyEffects** running (common for EQ, bass enhancement, noise reduction), check whether its plugins are contributing to the perceived audio quality issue:

```bash
# EasyEffects runtime state is stored in ~/.config/easyeffects/db/output.db
cat ~/.config/easyeffects/db/output.db 2>/dev/null | grep -E '^\[soe\]|^plugins=|^visible'

# This reveals:
# 1. The active plugin chain order (plugins= equalizer#0,exciter#0,limiter#0,...)
# 2. Which plugins are ON vs bypassed (bypass=true/false)
# 3. The plugin parameters (gain, frequency, Q, filter type)
```

**What to look for:**
- **Exciter** plugin — adds treble harmonics by design. A high `amount` (>2) with a high `scope` (>8000Hz) is actively adding artificial treble content. This can make the audio sound harsh, "sharp in the ear," or metallic (tin-can effect). If the user also has a high-shelf EQ or notch filter cutting the same treble region, these plugins are fighting each other.
- **Multiple EQ instances** — EasyEffects allows multiple `equalizer#N` instances. One may be boosting while another cuts overlapping frequencies. The `plugins=` line shows the order.
- **Bass Enhancer** — adds harmonic distortion to sub-bass frequencies. High `amount` (>8) with low `floor` (<30) and negative `inputGain` (< -5) suggests heavy processing that may be affecting midrange clarity.
- **Limiter** — with positive `inputGain` (>0), it's applying gain before limiting, which can squash dynamics and introduce pumping. Check `mode` (0=hard, 1=soft, 2=modern) and `attack`/`release` timings.

**Cross-reference with `pactl list short sinks`** — the `easyeffects_sink` virtual node appears as an extra sink. If applications are routing through `easyeffects_sink` (index X) → hardware sink (index Y), the EasyEffects chain is in the path.

**Pitfall:** EasyEffects plugin state is stored in a `.db` file (INI-like format), not in JSON presets. The `json` files under `~/.config/easyeffects/output/` are *presets* that can be loaded, but the *current running state* is separate in `~/.config/easyeffects/db/output.db`. Don't confuse the two — the `.db` file reflects what's actually applied right now.

### Step 4: Identify GPU audio device

```
# Find NVIDIA audio PCI device
lspci | grep -i 'audio.*nvidia\|nvidia.*audio'
# Example: 02:00.1 Audio device: NVIDIA Corporation GB206 High Definition Audio Controller

# Check if the audio module is loaded for NVIDIA
lsmod | grep snd_hda_intel
cat /proc/asound/cards  # Card 0 is usually NVIDIA HDMI, Card 1 is PCH/onboard
```

## Mitigation (No Reboot Required)

### Method 1: Unbind NVIDIA HDA Audio Device (immediate, runtime)

This removes the NVIDIA HDMI/DP audio device from the driver, eliminating its potential contribution to electrical noise. Requires root (via pkexec or sudo):

```bash
# Find the PCI address of the NVIDIA audio controller
# It's listed as "02:00.1" or similar in: lspci | grep -i audio
# Usually the .1 function of the GPU's PCI slot

# Unbind it from the snd_hda_intel driver
echo "0000:02:00.1" | sudo tee /sys/bus/pci/drivers/snd_hda_intel/unbind
# OR via pkexec:
pkexec sh -c 'echo "0000:02:00.1" > /sys/bus/pci/drivers/snd_hda_intel/unbind'
```

After unbinding:
- Card 0 (NVIDIA) disappears from `/proc/asound/cards`
- Onboard audio (Card 1, PCH) continues working normally
- The unbind takes effect instantly — no daemon restart needed

#### Restoring / Re-binding the NVIDIA Audio Device

If the user wants to undo the unbind (e.g., they use HDMI audio for a monitor or the unbind made things worse):

```bash
# Re-bind the NVIDIA audio device to the driver
echo "0000:02:00.1" | sudo tee /sys/bus/pci/drivers/snd_hda_intel/bind
# OR via pkexec:
pkexec sh -c 'echo "0000:02:00.1" > /sys/bus/pci/drivers/snd_hda_intel/bind'

# Verify it came back
cat /proc/asound/cards
# Should show: 0 [NVidia] -> HDA NVidia
#              1 [PCH]    -> HDA Intel PCH
```

If a blacklist file was created, also remove it and rebuild initramfs:

```bash
pkexec rm /etc/modprobe.d/nvidia-hdmi-audio-blacklist.conf
pkexec mkinitcpio -P                            # Arch/Manjaro
# OR
sudo update-initramfs -u                        # Debian/Ubuntu
```

**Pitfall:** After re-binding, the ALSA card topology reverts to its original state, but PipeWire may have custom sinks that reference `hw:1` by card index. If card 0 (NVIDIA) was missing temporarily and card 1 (PCH) temporarily became card 0 (because ALSA re-numbers), custom sinks using `hw:1` can get stuck in SUSPENDED even after re-bind. See the PipeWire restart section below.

### Method 2: Switch audio ports (free, worth trying)

Try the **opposite** physical port from what you're currently using:
- Rear line-out → front panel headphone jack (or vice versa)
- The front panel cable runs near the GPU and picks up *more* interference in many cases
- But sometimes the rear jack is electrically noisier due to different grounding

### Method 3: Restart PipeWire After Audio Device Changes (fix stuck sinks)

If the user unbound and re-bound the NVIDIA HDA device (or made any ALSA card topology change), custom PipeWire sinks using `hw:X` paths can get stuck in **SUSPENDED** state and refuse to wake up. Audio streams route to the sink but silence comes out.

To fix:

```bash
# Restart the PipeWire daemon and its PulseAudio compat layer
systemctl --user restart pipewire pipewire-pulse

# Verify sinks came back
pactl list short sinks

# Set the default sink back to the user's preference
pactl set-default-sink <SINK_NAME>       # e.g. alc1220-analog-sink

# Check sink state — should be IDLE or RUNNING when audio plays
pw-cli info <SINK_ID> | grep state
```

**Caveats:**
- Restarting PipeWire kills all current audio stream connections. Running apps (games, media players, browsers) will lose audio and need to re-establish playback (e.g., refresh tab, restart game audio).
- **EasyEffects** (`easyeffects_sink`) will also be killed — the `easyeffects_sink` virtual sink disappears entirely after `pipewire-pulse` restart. Restart EasyEffects separately:
  ```bash
  # If running as a systemd user service:
  systemctl --user restart easyeffects

  # If not running as a service, start it in the background:
  # (use terminal with background=true to start it)
  easyeffects --gapplication-service
  ```
  After restarting EasyEffects, the `easyeffects_sink` virtual sink re-appears. Verify with `pactl list short sinks | grep easy`.
- After restart, sinks start in SUSPENDED state — this is normal. They transition to IDLE when audio plays and RUNNING when actively playing.
- The `easyeffects_sink` virtual sink may appear with a new sink index number after restart. This doesn't affect routing if default sink is set by name, not index.

### Method 4: Mute NVIDIA ALSA device (less effective)

If you can't unbind the device, try muting its digital output:

```bash
amixer -c 0 set 'IEC958' mute  # Card 0 = NVIDIA
```

This is less effective than unbinding because the device is still active on the PCI bus.

## Permanent Fixes

### Fix 1: Blacklist the NVIDIA HDMI Audio Codec Module (recommended)

Prevents the driver from loading at all on next boot:

```bash
# Create blacklist file
pkexec tee /etc/modprobe.d/nvidia-hdmi-audio-blacklist.conf > /dev/null << 'EOF'
# Blacklist NVIDIA HDMI audio driver to prevent GPU coil whine interference
# with the onboard analog audio codec.
# The NVIDIA GPU's VRM switching noise couples through the motherboard
# ground plane into analog audio when under load.
blacklist snd_hda_codec_nvhdmi
EOF

# Rebuild initramfs for the change to take effect
pkexec mkinitcpio -P     # Arch/Manjaro
# OR
sudo update-initramfs -u  # Debian/Ubuntu
# OR
sudo dracut --force       # Fedora/RHEL
```

After reboot, verify:
```bash
cat /proc/asound/cards
# Should only show card 0 (or 1) as the PCH/onboard audio, no NVIDIA card
```

**Pitfall:** `snd_hda_intel` is shared between NVIDIA HDA and Intel PCH audio. Blacklisting `snd_hda_intel` would break ALL audio. Only blacklist the NVIDIA-specific codec module `snd_hda_codec_nvhdmi`.

### Fix 2: USB DAC (most effective hardware fix)

A USB DAC completely bypasses the motherboard's analog audio circuit:
- **Apple USB-C to 3.5mm dongle** (~$9) — surprisingly good DAC for the price
- Any USB audio adapter or external DAC/amp
- Digital audio is sent over USB, converted to analog **outside** the noisy PC case

This is the single most effective fix — works 99% of cases because the electrical path from GPU VRM to DAC is broken entirely.

### Fix 3: GPU Undervolt

Reducing GPU voltage reduces coil whine intensity at the source. On NVIDIA:
- Use the NVIDIA control panel or nvidia-settings to apply an undervolt curve
- Or use third-party tools (MSI Afterburner via Wine, or nvidia-smi power limits)
- Even a modest undervolt (reducing power limit by 10-15%) can significantly reduce whine

### Fix 4: External Audio Interface

A USB audio interface (Focusrite Scarlett, Behringer UMC, etc.) or external sound card replaces the entire onboard analog chain. More expensive than a USB dongle but offers better audio quality and typically zero noise.

## Verification

After any fix, verify by:
1. Launching a GPU-intensive game or stress test (e.g., `glxgears -info`, a game, or `nvidia-smi` stress test)
2. Listening for the buzzing/whining noise in headphones
3. Checking that system audio (music, notifications, game sounds) still works through the intended output

## Pitfalls

1. **Don't blacklist `snd_hda_intel`** — this module is shared between NVIDIA HDA and the Intel PCH audio controller. Blacklisting it kills ALL audio, including onboard. Only blacklist `snd_hda_codec_nvhdmi`.
2. **Don't confuse HDMI ground loop with analog interference** — If the user is using HDMI/DP audio (monitor speakers or monitor headphone jack), the issue is a ground loop through the HDMI/DP cable, not motherboard analog noise. Solutions differ: ferrite beads, ground loop isolator, or optical audio.
3. **Not all GPUs have audible coil whine** — coil whine depends on the specific GPU's VRM components, power supply quality, and the electrical load pattern. One RTX 5060 Ti may whine while another of the same model is silent.
11. **USB DAC won't fix HDMI-ground-loop noise** — If the user's audio goes through the monitor (HDMI/DP), a USB DAC plugged into the same PC but different audio output won't help the HDMI path.
12. **EasyEffects plugins can fight each other** — A common pattern: an Exciter adds treble harmonics (amount>2, scope>8kHz) while a separate EQ#N cuts the same 8-10kHz region by -5dB to -6dB. These work against each other — the Exciter adds artificial sharpness, the EQ tries to cut it — producing a lossy, phase-distorted signal that sounds "sharp in the ear" or "tin can hollow" despite EQ cuts. Check `~/.config/easyeffects/db/output.db` for this pattern before adding more EQ.
13. **EasyEffects .db file vs JSON presets** — EasyEffects stores *current running state* in `~/.config/easyeffects/db/output.db` (INI-like `[soe]` sections) and *saved presets* as `.json` files in `~/.config/easyeffects/output/`. These are independent — loading a JSON preset overwrites the `.db` state. When diagnosing, always read the `.db` file first to see what's actually applied now.
5. **EasyEffects/PipeWire noise gate is NOT a fix** — A noise gate or EQ filter in EasyEffects can mask low-level buzzing when idle, but the buzzing still reaches the DAC. The GPU electrical noise still affects analog signal integrity. Don't present this as a real fix.
6. **Check both front and rear audio ports** — Users often don't know which port they're using. Run `pactl list sinks | grep "Active Port"` to confirm. The front panel cable is a different physical path and may have different noise characteristics.
7. **Custom PipeWire sinks using `hw:X` change noise profile** — Custom `.conf` files in `~/.config/pipewire/pipewire.conf.d/` that create ALSA sinks with `api.alsa.path = "hw:1"` bypass the ALSA `front:X` mixer abstraction. This raw device access can make the codec's DAC more (or less) susceptible to ground-plane noise. Always test switching between the standard WirePlumber-managed sink and the custom sink during diagnosis.
8. **EasyEffects in the audio path doesn't change the electrical issue** — The `easyeffects_sink` virtual node acts as a pass-through filter. Applications route to it, then it routes to the hardware sink. This adds latency and a processing layer but does not change the electrical noise coupling — the DAC is still on the motherboard. Don't suggest modifying EasyEffects as a fix for electrical interference.
9. **Config file timestamps reveal recent changes** — Before deep-diving into hardware diagnosis, check `/var/log/pacman.log` or equivalent for recent audio stack updates (PipeWire, ALSA, kernel), and `stat` on PipeWire config files. A user reporting "it didn't happen before" often has a recently modified config or package update that changed the audio routing.
