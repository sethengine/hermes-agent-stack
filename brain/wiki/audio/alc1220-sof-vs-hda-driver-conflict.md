---
source: 20260701_180706_3fe888
category: audio
date: 2026-07-01
---

# ALC1220 on Intel 800 Series ACE: SOF vs snd_hda_intel Driver Conflict

The motherboard audio controller (Intel 800 Series ACE, PCI `8086:7f50`, class `0x040300`) fails when the SOF (Sound Open Firmware) driver is forced via `dsp_driver=3`.

**Root cause:** The ACE controller's PCI class `0x040300` does not match SOF's expected `0x040380`. SOF bails with `"the DSP is not enabled on this platform, aborting probe"`. Meanwhile, `snd_hda_intel` never gets a chance to bind. Result: no ALC1220 ALSA card.

**Fix:** Set `options snd-intel-dspcfg dsp_driver=0` (auto) or remove any `dsp_driver=3` config from `/etc/modprobe.d/snd-intel-dspcfg.conf`. The legacy `snd_hda_intel` driver handles the ALC1220 codec on the HDA bus directly — no DSP needed.

**Important:** The `dsp_driver` sysfs parameter at `/sys/module/snd_intel_dspcfg/parameters/dsp_driver` is read-only (`-r--r--r--`) after boot. Changing the driver selection requires a modprobe config change + reboot.

[[Z890-ACE-audio-diagnostic]] [[i915-blacklist-audio-deferred-probe]] [[PipeWire start-limit-hit]]
