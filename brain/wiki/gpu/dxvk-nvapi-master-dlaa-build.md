---
source: 20260706_194614_c828c3
category: gpu
date: 2026-07-12
tags: [dxvk-nvapi, dlaa, dlss, drs, r610, proton, ge-proton, nvidia, d2r, diablo-2]
---

# Building DXVK-NVAPI from Master for DLAA DRS Support

GE-Proton11-1 ships DXVK-NVAPI v0.9.2 (R595 headers), which does NOT recognize the `ngx_dlss_sr_override_render_preset_selection` DRS setting needed for DLAA. The DRS log shows:
```
0x10e41df2/Unknown = Setting not found
```

Building from git master (R610 headers) adds support for this setting plus a direct `NGX_DLAA_OVERRIDE`.

## Build Steps

```bash
git clone https://github.com/jp7677/dxvk-nvapi
cd dxvk-nvapi
meson setup build
meson compile -C build
# Output: build/src/dxvk-nvapi/nvapi64.dll
```

## Installation

Replace the bundled DLL in GE-Proton:
```bash
cp build/src/dxvk-nvapi/nvapi64.dll ~/.local/share/Steam/compatibilitytools.d/GE-Proton11-1/files/lib/wine/nvapi64.dll
```

## Verification

Check the new binary contains the expected DRS keys:
```bash
strings nvapi64.dll | grep -E "NGX_DLAA|RENDER_PRESET_[A-Z]"
```

## Launch Configuration

```ini
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=dlaa"
```

Use `dlaa` (not `ultra_quality`) as the preset value — the R610 headers recognize the explicit DLAA preset.

## Log Verification

Set `PROTON_LOG=1` and check `~/steam-<appid>.log` for:
```
Applying the following DRS settings (2 total):
    0x10e41e01/Enable DLSS-SR override = 0x1
    0x10e41df2/Enable DLSS-SR override render preset selection = DLAA
```

## No Visual Indicator on Linux

The DLSS debug overlay (`PROTON_DLSS_INDICATOR=1`) does not produce a visible screen overlay on Linux. The registry key only controls NGX debug logging. Confirm DLAA by comparing GPU usage at the same FPS cap (DLAA renders at native res = higher GPU load) or by visual sharpness comparison.

## References
- [[diablo-2-resurrected-dlaa-proton]]
- [[dlss-dll-replacement-ge-proton]]
- [[diablo-2-resurrected-proton-nvidia-wayland]]
- [[mangohud-fps-limiting-proton]]
