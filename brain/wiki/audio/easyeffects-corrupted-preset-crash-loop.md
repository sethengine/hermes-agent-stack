---
source: 20260703_231509_6397bb
category: audio
date: 2026-07-03
tags: [easyeffects, crash-loop, corrupted-preset, max-quality, ini, json]
---

# EasyEffects Crash Loop from Corrupted Preset File

EasyEffects enters an infinite crash-restart loop when its output preset file `max_quality.json` is corrupted. The file contains INI-format content (`[General]...`) instead of valid JSON.

**Symptoms:** EE crashes with SIGABRT, systemd auto-restarts it, crashes again on the same file — repeat. 5 consecutive crashes observed with core dumps of 15-30 MB each.

**Root cause:** `~/.local/share/easyeffects/output/max_quality.json` starts with bytes `5b 47` = `[G` (INI section header), not `{` (JSON object). EE's JSON parser immediately fails.

**Fix:** Delete the corrupted file:
```
rm "/home/sethengine/.local/share/easyeffects/output/max_quality.json"
```

**Prevention:** After removing, create a fresh preset within EE and verify it's valid JSON before saving.

[[easyeffects-crash-missing-sink]]
[[pipewire-start-limit-hit-recovery]]
