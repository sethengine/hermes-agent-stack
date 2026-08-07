---
source_session: 20260706_194614_c828c3
date: 2026-07-12
category: gpu
tags: [diablo-2, d2r, dlaa, dlss, dxvk-nvapi, nvidia, proton, wayland, drs, launch-options]
---

# D2R DLAA via Named DXVK-NVAPI Env Var Overrides (Production Config)

The `DXVK_NVAPI_DRS_SETTINGS` syntax (`ngx_dlss_sr_override=on,...`) is one way to force DLAA in Diablo 2 Resurrected. However, the named individual env vars are a simpler alternative that works with GE-Proton (bundles DXVK-NVAPI v0.9.2+).

## Working Launch Options

```
DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1 DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1 mangohud %command%
```

**Both overrides are required:**
- `DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1` — enables the DLSS super-resolution pipeline
- `DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1` — forces the pipeline into DLAA mode (native res temporal AA)

Without the SR override, the DLAA override is silently ignored.

## In-Game Settings

| Setting | Value | Why |
|---------|-------|-----|
| NVIDIA DLSS | Quality (or any) | DLSS pipeline must be active |
| Resolution Scale | 100% | Already defaults correctly |
| Anti Aliasing | Off | DLAA replaces it |
| VSync | Off | MangoHud handles frame cap |

## Verification

Set `PROTON_LOG=1` and check `~/steam-<appid>.log` for:

```
0x10e41df4/Override DLSS mode to be DLAA = 0x1
```

No visual overlay indicator exists on Linux. Confirm by comparing GPU load at same FPS cap (DLAA = native resolution = higher GPU usage).

## References
- [[diablo-2-resurrected-dlaa-proton]] — DRS_SETTINGS alternative
- [[dxvk-nvapi-master-dlaa-build]] — building DXVK-NVAPI for R610 DLA support
- [[diablo-2-resurrected-proton-nvidia-wayland]]
