---
source: "20260704_212250_ef6734"
date: "2026-07-04"
category: "software"
---

# Dead Space Remake HDR with GameScope on KDE Wayland + NVIDIA

Running Dead Space Remake (DX12) with HDR on Manjaro KDE Wayland + NVIDIA.

## Working Configuration

### Steam Launch Options

```sh
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- env VKD3D_CONFIG=hdr PROTON_ENABLE_NVAPI=1 %command%
```

### Proton Version
GE-Proton11-1

### HDR Setup
- **Do NOT enable desktop HDR** — `gamescope --hdr-enabled` handles it per-game
- Desktop: `kscreen-doctor output.DP-3.hdr.enable` / disable (should stay off)
- In-game: Settings → Display → HDR: On
- Peak luminance: ~400 nits
- Optional: `--hdr-itm-enable` for inverse tone mapping (SDR→HDR conversion)

### System
- NVIDIA 595.71.05 (explicit sync, HDR-capable)
- KDE Plasma 6.6.5 (Native Wayland HDR)
- gamescope 3.16.24
- GE-Proton11-1 installed in Steam compat tools
- Display: DP-3, 3440×1440 @ 165Hz

## Related
- [[nvidia-dmar-fault-crash-cascade]]
