---
source: 20260706_194614_c828c3
category: software
date: 2026-07-06
tags: [diablo-2, proton, nvidia, wayland, gaming, steam, fullscreen, ge-proton]
---

# Diablo 2 Resurrected: Proton Settings for NVIDIA Wayland

D2R on NVIDIA + Wayland has known issues with fullscreen, resolution, and frame limiter under Proton.

## Fullscreen/Resolution Fix

The fullscreen bug (fixed window, no resolution options) is a known Proton 10 issue on NVIDIA. Workarounds:
- Switch to **Proton Experimental** (Steam → D2R → Properties → Compatibility)
- Or **GE-Proton10-34** (confirmed fix for RTX 4070 + NVIDIA 595)
- `Alt+Enter` toggles windowed→fullscreen (fixes 1/4-screen render bug)
- Add `PROTON_ENABLE_WAYLAND=0 %command%` to launch options

## Battle.net Login

On fresh install, create the ClientSDK folder manually:
```bash
mkdir -p "/path/to/pfx/drive_c/users/steamuser/AppData/Local/Blizzard Entertainment/ClientSdk"
```

## Vsync

Turn off Vsync in-game — causes FPS drops and instability on NVIDIA.

## References
- [[linux-gaming-frame-limiters]]
- [[geforce-rtx-5060-ti]]
