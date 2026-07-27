# PipeWire + Audio Diagnostics Reference

## Symptoms

- `pw-top` shows ERR > 0 on sink nodes
- `journalctl --user -u pipewire` shows `spa.alsa: 'front:1': playback open failed: Device or resource busy`
- `journalctl --user -u pipewire` shows `error in config '...conf': Expected object key`
- `journalctl --user -u wireplumber` shows `link failed: 1 of 1 PipeWire links failed to activate` or `proxy destroyed`
- `pw-top` shows no audio flowing but sinks are marked RUNNING

## Diagnostic Commands

```bash
# 1. Check PipeWire config errors
journalctl --user -u pipewire --since -1h --no-pager | grep -iE 'error|fail|warn'

# 2. Check WirePlumber link failures
journalctl --user -u wireplumber --since -1h --no-pager | grep -iE 'error|fail|warn'

# 3. List all nodes (sinks/sources) and their state
pw-cli list-objects Node | grep -E 'node.name|state|error' | head -40

# 4. Check which devices are contending for the same ALSA device
grep -rn 'front:1\|hw:1' ~/.config/pipewire/ /etc/pipewire/ ~/.config/wireplumber/ 2>/dev/null

# 5. Check ALSA device availability
aplay -l
cat /proc/asound/cards

# 6. List all PipeWire config files in the conf.d chain
ls -la ~/.config/pipewire/pipewire.conf.d/
```

## Known Failure Patterns

### Pattern A: Unquoted enum values in `context.objects`

**Error:** `error in config 'alsa-sink-alc1220.conf': Expected object key`

**Cause:** In SPA-JSON config, string values in `args = { ... }` blocks MUST be quoted. An unquoted value like `resample.method = soxr` is parsed as an object key, not a string value.

**Fix:** Either quote string values or use numeric equivalents:
```conf
# BROKEN — parser reads "soxr" as a key
resample.method = soxr
resample.quality = 10

# FIXED — use only the quality number (10 = soxr-vhq)
resample.quality = 10

# OR quote the string
resample.method = "soxr"
resample.quality = 10
```

### Pattern B: WirePlumber auto-sink vs manual sink on same ALSA device

**Error:** `spa.alsa: 'front:1': playback open failed: Device or resource busy` (repeated 25+ times)

**Cause:** WirePlumber creates an auto-detected sink (e.g., `alsa_output.pci-0000_80_1f.3.analog-stereo`) that opens `front:1` during node detection. A manually-defined `context.objects` sink also uses `api.alsa.path = "front:1"`. The second open fails because the first holds the PCM device.

**Fix Option A** — Disable WirePlumber auto-sink for the Intel HDA card:
Create `~/.config/wireplumber/wireplumber.conf.d/90-disable-auto-intel-hda.conf`:
```
monitor.alsa.rules = [
    {
        matches = [
            { device.name = "alsa_card.pci-0000_80_1f.3" }
        ]
        actions = { create-node = false }
    }
]
```

**Fix Option B** — Use `hw:1,0` instead of `front:1` in the manual config:
```conf
api.alsa.path = "hw:1,0"
```
This accesses the raw device directly, avoiding the front PCM contention.

**Fix Option C** — The `99-audio-quality.conf` or similar AutoProfiile config may also contend. Check all files in `~/.config/pipewire/pipewire.conf.d/` for duplicate `api.alsa.path` references.

### Pattern C: DMAR INTR-REMAP faults from NVIDIA HDA audio

**Error (in `dmesg`):**
```
DMAR: DRHD: handling fault status reg 2
DMAR: [INTR-REMAP] Request device [02:00.1] fault index 0x...
  Present field in the IRTE entry is clear
```
Device `02:00.1` = NVIDIA GB206 HDA Audio Controller (HDMI audio on the GPU).

**Cause:** `intel_iommu=on` + NVIDIA GPU audio function. The IOMMU interrupt remapping table entries for the NVIDIA HDA device get corrupted, causing continuous fault interrupts at the kernel level. The faults fire even when no audio is routed through HDMI.

**Impact:** Constant kernel IRQ handler cycles — measurable CPU overhead (~0.5-1%), unnecessary interrupt processing, and 4 unused PipeWire sinks (pro-output-3/7/8/9) that can't be suspended because the hardware is faulting.

**Fix:** Since HDMI audio is not used (audio goes through the motherboard ALC1220 codec), disable the NVIDIA HDA audio device:
```bash
# Hot-unbind (immediate, temporary):
echo 1 | sudo tee /sys/bus/pci/devices/0000:02:00.1/remove

# Persistent via modprobe (survives reboot):
echo 'options snd_hda_intel enable=0,1' | sudo tee /etc/modprobe.d/nvidia-hda.conf
sudo mkinitcpio -P && reboot
```

**Verification:**
```bash
dmesg | grep -c 'DMAR.*INTR-REMAP'    # should be near 0 after fix
aplay -l                               # card 0 (NVidia) should be gone
pw-cli list-objects Node | grep pro-output  # should show 0 entries
```

## Verification After Fix

```bash
# No config errors
journalctl --user -u pipewire --since -10m | grep -c "error in config"

# No ALSA device busy
journalctl --user -u pipewire --since -10m | grep -c "Device or resource busy"

# No WirePlumber link failures
journalctl --user -u wireplumber --since -10m | grep -c "link failed"

# ERR column in pw-top should be 0 for all sinks
pw-top -b -n 1 | awk '{print $9, $10}' | grep -v "^0"

# pw-dump should show only the working sink
pw-dump | python3 -c "
import sys, json
d = json.load(sys.stdin)
for n in [x for x in d if x.get('type')=='PipeWire:Interface:Node']:
    e = n.get('info',{}).get('error','ok')
    if e != 'ok':
        print(f'ERROR: {n.get(\"info\",{}).get(\"props\",{}).get(\"node.name\",\"?\")}: {e}')
"
```
