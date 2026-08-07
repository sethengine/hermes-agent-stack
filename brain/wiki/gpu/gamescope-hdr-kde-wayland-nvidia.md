---
source: "20260704_212250_ef6734"
date: "2026-07-04T22:10:53+00:00"
category: "gpu"
related: ["proton-prefix-corruption", "vkd3d-shader-compilation-stutter", "gamescope-xwayland-overhead"]
---

# Gamescope HDR on KDE Wayland with NVIDIA

Running Windows games with HDR via gamescope on Manjaro KDE Wayland with NVIDIA requires specific configuration.

## Desktop HDR Toggle

Desktop HDR must be enabled before launching (KWin/NVIDIA limitation):
```sh
kscreen-doctor output.DP-3.hdr.enable   # enable before game
kscreen-doctor output.DP-3.hdr.disable  # disable after quitting
```

## Working Launch Options

Base configuration without desktop HDR (HDR ITM mode):
```
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --hdr-itm-enable --adaptive-sync --steam -- env VKD3D_CONFIG=hdr %command%
```

With performance tuning (no VKD3D_CONFIG=hdr — redundant via gamescope HDR swapchain):
```
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --rt --nvidia-disable-gsp --steam -- env PROTON_ENABLE_NVAPI=1 VKD3D_CONFIG=async %command%
```

## HDR ITM (Inverse Tone Mapping)

`--hdr-itm-enable` allows HDR output without desktop HDR being enabled — useful on KWin/NVIDIA where desktop HDR toggle has side effects.

## Verification

gamescope exposes HDR via `VK_FORMAT_R16G16B16A16_SFLOAT` swapchain. Log confirmation:
```
server hdr output enabled:     true
hdr formats exposed to client: true
```
