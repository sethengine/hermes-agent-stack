---
source: 20260701_180706_3fe888
category: kernel
date: 2026-07-01
---

# i915 Blacklist Causes snd_hda_intel Deferred Probe on Intel ACE Audio

With `blacklist i915` in `/etc/modprobe.d/blacklist-i915.conf`, the `snd_hda_intel` driver for the Intel 800 Series ACE audio controller (PCI `0000:80:1f.3`) gets stuck in deferred probe.

**Root cause:** `snd_hda_intel` tries to bind to `i915`'s audio component interface during probe. Since `i915` is blacklisted, it never loads to register this component. The HDA driver's probe is deferred indefinitely — `"deferred probe pending: snd_hda_intel: couldn't bind with audio component"`. The ALC1220 codec (`snd_hda_codec_alc882`) initialization never runs.

**Evidence:** Boots with `i915` loaded (but failing GPU probe gracefully) always detect the ALC1220. Boots with `i915` blacklisted sometimes succeed (if probe timing beats the component timeout) and sometimes don't — the race depends on IOMMU group ordering.

**Fix:** Remove the `blacklist i915` line. `i915` will load, register the audio component, then fail GPU probe gracefully — but the audio component registration survives.

[[ALC1220-SOF-vs-HDA-driver-conflict]] [[Z890-ACE-audio-diagnostic]]
