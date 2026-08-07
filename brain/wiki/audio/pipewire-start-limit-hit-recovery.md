---
source: 20260701_180706_3fe888
category: audio
date: 2026-07-01
---

# PipeWire Systemd Start-Limit-Hit Recovery

PipeWire can hit systemd's `start-limit-hit` when it repeatedly fails to start due to ALSA config issues (e.g., referencing `hw:1` that doesn't exist after ALC1220 disappeared).

**Symptoms:** `pactl info` returns "Connection refused". `systemctl --user status pipewire.service` shows "start-limit-hit". Journal shows `spa.alsa: 'hw:1': playback open failed: No such file or directory` and `pw.conf: can't create object from factory adapter: Invalid argument`.

**Recovery steps:**
1. Remove stale socket files: `rm -f /run/user/1000/pipewire-0*`
2. Reset systemd start limit: `systemctl --user reset-failed pipewire.service pipewire.socket wireplumber.service`
3. Start services: `systemctl --user start pipewire.socket pipewire.service wireplumber.service`

**Prevention:** Ensure PipeWire config doesn't reference ALSA device `hw:1` by card index, as card enumeration can change between boots — use pipewire node names instead.

[[ALC1220-SOF-vs-HDA-driver-conflict]] [[Z890-ACE-audio-diagnostic]]
