---
source: 20260701_180706_3fe888
category: audio
date: 2026-07-01
---

# EasyEffects Crash When Audio Sink Disappears

EasyEffects crashes with a SIGSEGV when its configured output sink node (e.g., `alc1220-analog-sink`) disappears because the underlying ALSA device is no longer available.

**Symptoms:** Coredump from `easyeffects` daemon. Stack trace shows crash in `lsp-plugins-lv2.so` (spectrum analyzer / compressor plugin) in thread 9800 at `clock_nanosleep`. The crash cascades — PipeWire and WirePlumber exit, and the entire audio stack enters start-limit-hit.

**Root cause:** EasyEffects holds references to PipeWire nodes by name/ID. When the hardware is removed (driver change, unbind), the node goes away. EasyEffects' LV2 plugin chain doesn't handle the stale node reference gracefully.

**Fix:** Disable or reconfigure EasyEffects to use a fallback sink before removing hardware. Or restart EasyEffects after the audio stack is restored.

[[PipeWire start-limit-hit recovery]]
