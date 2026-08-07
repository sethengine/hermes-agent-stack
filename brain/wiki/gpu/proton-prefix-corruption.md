---
source: "20260704_212250_ef6734"
date: "2026-07-04T22:10:53+00:00"
category: "gpu"
related: ["gamescope-hdr-kde-wayland-nvidia", "vkd3d-shader-compilation-stutter"]
---

# Proton Prefix Corruption from GE-Proton Version Mismatch

Switching GE-Proton versions (e.g., GE-Proton11-1 → GE-Proton10-34) corrupts the Steam compatdata prefix, causing silent game crashes.

## Symptoms

- Game shows gamescope yellow W fallback icon (silent crash)
- Log: "Proton: Prefix has an invalid version?!"
- "Upgrading prefix from X to Y" message in Proton log

## Fix

Delete the corrupted compatdata directory — Steam recreates it on next launch:

```sh
rm -rf "/home/sethengine/.local/share/Steam/steamapps/compatdata/<GAME_APPID>"
```

Then set a fixed Proton version in Steam → Game Properties → Compatibility to prevent accidental version switching.

## Prevention

Always set a specific GE-Proton version per-game in Steam Properties rather than relying on the global default, which may change between Proton-GE releases.
