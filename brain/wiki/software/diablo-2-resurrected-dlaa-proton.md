---
source: 20260706_194614_c828c3
category: software
date: 2026-07-09
tags: [diablo-2, proton, nvidia, wayland, dlaa, dlss, dxvk-nvapi, optiscaler, anti-aliasing]
---

# Diablo 2 Resurrected: DLAA via DXVK-NVAPI / OptiScaler on Proton

D2R has no native DLAA toggle but can be forced into DLAA mode (DLSS at native resolution with temporal AA) via driver overrides.

## D2R DLSS settings (Settings.json)

```
"NVIDIA DLSS": 2,     // 1=Performance, 2=Quality, 3=Balanced, 4=Ultra Performance
"Resolution Scale": 100,
"Anti Aliasing": 0,    // 0 = off (DLSS replaces it)
```

No native DLAA option exists in the menu. The 310.7.0.0 DLSS DLL includes DLAA render presets (Preset E/J).

## Method 1: In-game Quality + 100% scale (approximate)

Set DLSS to Quality + 100% Resolution Scale. Not true DLAA preset but visually very close.

## Method 2: DXVK-NVAPI driver override (recommended)

Add to Steam launch options:
```
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=ultra_quality" mangohud %command%
```

This forces the DLAA ultra-quality render preset through DXVK-NVAPI. Works with GE-Proton (already includes DXVK-NVAPI).

## Method 3: OptiScaler Quality Ratio trick

In `OptiScaler.ini`:
```ini
Dx12Upscaler=dlss
QualityRatio=1.01
```

The `1.01` (not 1.0) prevents the game from disabling DLSS when render resolution matches display resolution.

## References
- [[diablo-2-resurrected-proton-nvidia-wayland]]
- [[diablo-2-resurrected-community-fixes]]
- [[dlss-dll-replacement-ge-proton]]
- [[linux-gaming-frame-limiters]]
