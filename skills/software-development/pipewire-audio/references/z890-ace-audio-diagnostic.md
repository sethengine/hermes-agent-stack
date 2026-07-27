# Z890 ACE Audio Controller — Diagnostic Reference

## Platform

- **Motherboard**: Gigabyte Z890 AERO G
- **Audio codec**: Realtek ALC1220 (via Intel 800 Series ACE)
- **GPU**: NVIDIA RTX 5060 Ti (PCI `0000:02:00.1`) — discrete only, no Intel iGPU
- **CPU**: Arrow Lake-HX (KF-series, no integrated graphics)
- **Kernel**: 7.0.10-1-MANJARO (upgraded from 6.18)
- **OS**: Manjaro Linux
- **PipeWire**: 1.6.5-2

## PCI Topology

```
00:1f.0 ISA bridge: Intel Corporation Z890 Chipset LPC/eSPI Controller [8086:7f04]
80:1f.3 Audio device: Intel Corporation 800 Series ACE (Audio Context Engine) [8086:7f50] (rev 10)
  Class: 0x040300 (generic multimedia audio — NOT DSP-enabled)
  Kernel modules: snd_sof_pci_intel_mtl, snd_hda_intel
  Driver: none (unbound after diagnostic)

02:00.1 Audio device: NVIDIA Corporation GB206 High Definition Audio Controller (rev a1)
  Driver: snd_hda_intel (working)
```

## Diagnostic Steps

### 1. Check audio PCI devices

```bash
lspci | grep -i "audio\\|HDMI\\|hda"
# 02:00.1 Audio device: NVIDIA Corporation GB206...
# 80:1f.3 Audio device: Intel Corporation 800 Series ACE...
```

### 2. Check ALSA cards

```bash
cat /proc/asound/cards
# 0 [NVidia]: HDA-Intel - HDA NVidia
# (only NVIDIA — no Intel card)
```

### 3. Check current default audio sink

```bash
pactl info | grep "Default Sink"
# Default Sink: alsa_output.pci-0000_02_00.1.pro-output-3 (GPU HDMI)

pactl list short sinks
# 31  gb206-audio-sink (SUSPENDED)        ← custom GPU F32 sink
# 54  alsa_output.pci-0000_02_00.1...     (RUNNING) ← active GPU HDMI
# 55-57 other GPU 8ch sinks (SUSPENDED)

pactl list short sink-inputs
# 281 → sink 54 (GPU HDMI active stream)
```

### 4. Check driver binding and hardware

```bash
# Driver state for Intel ACE
readlink -f /sys/bus/pci/devices/0000:80:1f.3/driver
# → initially: snd_hda_intel (then unbound, unbound thereafter)
# (no driver auto-rebounds after unbind)

# PCI class code
cat /sys/bus/pci/devices/0000:80:1f.3/class
# 0x040300

# Module matching
lspci -v -s 80:1f.3 | grep "Kernel modules"
# Kernel modules: snd_sof_pci_intel_mtl, snd_hda_intel

# SOF firmware available
ls /lib/firmware/intel/sof-ipc4/mtl/
# sof-mtl.ri (present)
```

### 5. Check kernel logs

```bash
journalctl -k --no-pager | grep -i "1f\\.3\\|hda.*intel"
# Key lines:
# snd_hda_intel 0000:80:1f.3: Force to snoop mode by module option (×4 — retries)
# pci 0000:80:1f.3: deferred probe pending: snd_hda_intel: couldn't bind with audio component

# After unbinding from snd_hda_intel:
# sof-audio-pci-intel-mtl 0000:80:1f.3: enabling device (0000 -> 0002)
# sof-audio-pci-intel-mtl 0000:80:1f.3: the DSP is not enabled on this platform, aborting probe
```

### 6. Module parameters in effect

```bash
cat /sys/module/snd_intel_dspcfg/parameters/dsp_driver
# 0 (auto)

cat /etc/modprobe.d/snd-hda-intel.conf
# options snd_hda_intel enable_msi=1
# options snd_hda_intel power_save=0
# options snd_hda_intel power_save_controller=0
# options snd_hda_intel position_fix=1     ← may interfere with ACE
# options snd_hda_intel bdl_pos_adj=32      ← may interfere with ACE
# options snd_hda_intel snoop=1             ← may interfere with ACE
```

### 7. SOF driver check source (archived knowledge)

In `sound/soc/sof/intel/hda.c`:

```c
if (pci->class != 0x040100 && pci->class != 0x040380) {
    dev_err(sdev->dev, "the DSP is not enabled on this platform, aborting probe\\n");
    return -ENODEV;
}
```

- `0x040100` = HDA (legacy)
- `0x040380` = HDA + DSP (SOF-capable)
- Device reports `0x040300` → rejected

## Attempted Fixes

### What worked partially

1. Creating `/etc/modprobe.d/snd-intel-dspcfg.conf` with `options snd-intel-dspcfg dsp_driver=3`
   - Wrote via `pkexec tee` (sudo required password)
   - Takes effect on next boot, but SOF still fails with "DSP not enabled"

2. Unbinding from `snd_hda_intel`:
   - `pkexec sh -c 'echo 0000:80:1f.3 > /sys/bus/pci/drivers/snd_hda_intel/unbind'`
   - Unbind succeeded (device became unbound)
   - SOF auto-probed but failed (DSP not enabled)
   - No driver auto-bound after SOF rejection
   - `pkexec` timed out during the operation (GUI dialog)

### What didn't work

- `/sys/module/snd_intel_dspcfg/parameters/dsp_driver` — **permissions `-r--r--r--` (read-only)** — even with root the file is not writable on this kernel (7.0.10-1-MANJARO). Confirmed by `ls -la`. The parameter is baked in at module load time via modprobe.d or kernel cmdline.
- `echo 0000:80:1f.3 > /sys/bus/pci/drivers/snd_hda_intel/bind` → **"No such device"** — after unbinding from the SOF driver, manually binding to snd_hda_intel failed because the dsp_driver=3 redirect wasn't re-evaluated. The device stayed unbound.
- `systemd-run --user --scope` failed (unknown assignment)
- `sudo` required password in non-interactive terminal
- `pkexec bash -c 'echo 4 > /sys/module/snd_intel_dspcfg/parameters/dsp_driver'` → `Not authorized` (polkit refused)
- `pkexec sh -c '...'` timed out (GUI dialog hung in non-interactive context)

## Root Cause Summary

The ALC1220 is inaccessible because **both possible drivers fail on auto** — this is a two-failure deadlock unique to dGPU-only systems with the ACE controller:

1. **BIOS doesn't enable DSP mode** on the Intel 800 Series ACE controller
2. Without DSP mode, the PCI class is `0x040300` instead of `0x040380`
3. The SOF driver rejects `0x040300` with "DSP is not enabled on this platform"
4. The legacy `snd_hda_intel` driver also fails because it needs the i915/Xe display audio component, which doesn't exist on a dGPU-only system (no Intel iGPU)
5. No third driver (AVS at dsp_driver=4) was tested

## Working Fix

On the Gigabyte Z890 AERO G with dGPU-only (no Intel iGPU), the actual working fix was `dsp_driver=1` (force legacy HDA):

```bash
echo 'options snd-intel-dspcfg dsp_driver=1' | sudo tee /etc/modprobe.d/snd-intel-dspcfg.conf
sudo mkinitcpio -P   # rebuild initramfs
sudo reboot
```

This is counterintuitive — the ACE controller is a SOF-era device, but when SOF's DSP check blocks (class `0x040300`), forcing `snd_hda_intel` via `dsp_driver=1` bypasses SOF entirely and the legacy driver successfully drives the ALC1220 codec.

### Post-fix: ALSA card state

```
cat /proc/asound/cards
 0 [NVidia         ]: HDA-Intel - HDA NVidia
 1 [PCH            ]: HDA-Intel - HDA Intel PCH      ← restored!
```

PipeWire auto-detects: `alsa_output.pci-0000_80_1f.3.analog-stereo`
Custom sink `alc1220-analog-sink` (via `~/.config/pipewire/pipewire.conf.d/`) shows as RUNNING.

### Post-fix: Right channel mute on headphones

After `dsp_driver=1` fix, the ALC1220 routes correctly but **Headphone output volume defaults to 0**. The ALSA simple mixer "Headphone" control is unreliable — it reports setting values correctly while the hardware register stays at 0. Always use direct numid access:

```bash
amixer -c1 cset numid=3 87,87    # Headphone Playback Volume → both channels 100%
amixer -c1 cset numid=4 on,on    # Headphone Playback Switch → unmuted
```

To persist across reboots, add to `/etc/alsa/state/he1rt` or use `alsactl store`.

## Side Effects of the Fix

- EasyEffects crashed (SIGABRT from `lsp-plugins-lv2.so`) during PipeWire restart — the plugin chain truncated after crash, requiring manual re-selection of the output device in EE
- PipeWire socket files (`/run/user/$UID/pipewire-0*`) persisted after crash and blocked restart until manually removed
- `systemctl --user reset-failed pipewire pipewire-pulse wireplumber` needed before services would start again

## Related Kernel Changes

- Kernel 6.18 → 7.0 upgrade on May 30 (via `linux-meta 6.18-1 → 7.0-1`) may have triggered the regression
- SOF firmware upgrade: `sof-firmware 2025.12-1 → 2025.12.2-1` on Feb 14
- The Arch Linux forum [thread 292453](https://bbs.archlinux.org/viewtopic.php?id=292453) confirms `i915.modeset=0` (disabling iGPU) causes "couldn't bind with audio component" on snd_hda_intel

## Future Investigation

- Test `dsp_driver=4` (AVS) — alternative Intel SOC audio driver
- Test `dsp_driver=1` (force legacy HDA) — may behave differently from auto
- Test removing `snoop=1` and `position_fix=1` from snd_hda_intel options (they're applied globally and may break ACE)
- Test with `i915` loaded (if BIOS has "Multi-Monitor" or "iGPU" enable for the Intel graphics)
- Check if Gigabyte BIOS settings "Audio DSP" exists under Peripherals or Settings → Miscellaneous
