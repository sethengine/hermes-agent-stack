---
name: nvidia-proton-gaming
version: "1.0.0"
description: "Troubleshoot and optimize NVIDIA + Proton gaming on Linux (Wayland, KDE). DLSS/DLAA override, DXVK-NVAPI build, DRS env vars, MangoHud, shader cache."
allowed-tools: terminal, read_file, search_files, write_file, patch, web_search
---

# NVIDIA + Proton Gaming on Linux

## Diagnosing Performance Issues

### After Driver Upgrade
NVIDIA driver upgrades (e.g., 595→610) invalidate the VKD3D-Proton Vulkan pipeline cache and the DXVK state cache. First launch after upgrade will stutter heavily — shaders compile on-the-fly.

**Fix:** Play through different areas for 20-30 minutes. Each shader only stutters once. Check cache size at:
```
~/.local/share/Steam/steamapps/shadercache/<APPID>/nvidiav1/
```

Clear the empty stub cache after driver upgrade:
```
rm -f "<game-dir>/vkd3d-proton.cache"
rm -f "<game-dir>/vkd3d-proton.cache.write"
```

### Low GPU Usage + Low FPS (GPU stalling)
Check `nvidia-smi`:
- If GPU power draw is far below the power limit (e.g., 89W of 184W) with performance state P0 → shader compilation bottleneck or CPU/Vulkan pipeline stall
- If clocks are normal (2752 MHz+ for 5060 Ti) but utilization is low → likely shader cache rebuilding

### nvidia-powerd
`nvidia-powerd` is for **laptops only** (Dynamic Boost — shared CPU/GPU power budget). Desktop GPUs (including RTX 5060 Ti) are NOT supported. It will log `ERROR! Running on an unsupported system (PCI device Id: 0x....)` and exit immediately. Do not enable.

---

## DLSS DLL Upgrade

DLSS DLLs can be upgraded via the loathingkernel manifest (same source GE-Proton uses internally):

```
Manifest: https://loathingkernel.github.io/proton-upscalers/manifest.json
```

Latest versions (as of mid-2026):
- `nvngx_dlss.dll` (Super Resolution): 310.7.0.0 (CL 37997616)
- `nvngx_dlssg.dll` (Frame Gen): 310.7.0.0 (CL 37935832)
- `nvngx_dlssd.dll` (Depth): 310.7.0.0 (CL 37996128)

**Key:** The manifest entries have `version_number` for proper sorting. Filter `is_dev_file=false`.

Download example (Python):
```python
url = f'https://loathingkernel.github.io/proton-upscalers/manifest.json'
# Parse JSON, filter non-dev, sort by version_number descending
# .xz files, decompress with lzma module
```

**Replace the DLL in the game directory** next to the game exe. The Windows DLL search order loads from the game dir first. No WINEDLLOVERRIDES needed.

---

## DLAA Override (Native Res DLSS as Anti-Aliasing)

### Requirements
- DXVK-NVAPI that supports R610 DRS headers (v0.9.2 is NOT enough, needs git master)
- GE-Proton or Proton with NVAPI enabled (auto-enabled in GE-Proton11.1+)
- Game must have DLSS option enabled in menu (DLSS pipeline needs to be active)

### Build DXVK-NVAPI from source for new DRS support
```bash
git clone --recurse-submodules https://github.com/jp7677/dxvk-nvapi.git
cd dxvk-nvapi
./package-release.sh master /tmp/dxvk-nvapi-build
# Replace in GE-Proton:
cp /tmp/dxvk-nvapi-build/dxvk-nvapi-master/x64/nvapi64.dll \
   ~/.local/share/Steam/compatibilitytools.d/GE-Proton*/files/lib/wine/nvapi/x86_64-windows/nvapi64.dll
```

### DRS Env Vars for DLAA
```
DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1     # Enable DLSS Super Resolution (required)
DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1         # Force DLAA mode (native res AA)
```

These map to NVAPI DRS setting IDs:
- `0x10E41E01` = NGX_DLSS_SR_OVERRIDE_ID
- `0x10E41DF4` = NGX_DLAA_OVERRIDE_ID (value DLAA_ON = 1)

Steam launch option example:
```
DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1 DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1 PROTON_ENABLE_WAYLAND=1 mangohud %command%
```

**Check if it's working** via Proton log (`PROTON_LOG=1`):
```
grep -i "dlaa\|0x10e41df4" ~/steam-<APPID>.log
```
Expected output: `Override DLSS mode to be DLAA = 0x1` and `OK` on the GetSetting call.

### Render Preset Values
Available render presets in R610 headers:
- `RENDER_PRESET_A` through `RENDER_PRESET_Z` (letter presets)
- `RENDER_PRESET_Default`, `RENDER_PRESET_Latest`
- `DLAA_ON`, `DLAA_DEFAULT` (for DLAA override)
- `OFF`, `ON`, `AUTO`, `MIN`, `MAX`

### In-Game Settings for DLAA
- NVIDIA DLSS: set to Quality (or any mode — DLSS pipeline must be active)
- Resolution Scale: 100%
- Anti Aliasing: Off (DLAA replaces it)
- VSync: Off (MangoHud handles frame cap)

---

## MangoHud Frame Limiting

### Config (`~/.config/MangoHud/MangoHud.conf`)
```ini
fps_limit=164              # Set to your display refresh rate - 1
fps_limit_method=early     # Better frame pacing than 'late'
# vulkan_present_mode=immediate  # DO NOT use this with fps_limit — it bypasses the cap
no_display=1               # Hide HUD but keep the cap
```

### Per-Game Override
Use env var in launch option (takes priority over config file):
```
MANGOHUD_CONFIG="fps_limit=60,fps_limit_method=early,no_display=1" mangohud %command%
```

### Why Game Frame Limiters Don't Work on Proton
Most in-game frame limiters use CPU-side `Sleep()` calls. Under Wine/Proton:
- Sleep timers are imprecise
- VKD3D-Proton's swapchain buffer decouples from game timing
- Wayland + NVIDIA adds another layer of presentation indirection

MangoHud hooks at the Vulkan `vkQueuePresentKHR()` layer — it works regardless of what the game does.

---

## Useful NVAPI DRS Settings (R610+)
| Setting | Env Var | ID | Purpose |
|---------|---------|-----|---------|
| DLSS SR override | `DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE` | 0x10E41E01 | Enable DLSS Super Resolution |
| DLAA mode | `DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE` | 0x10E41DF4 | Force DLAA (native res AA) |
| SR preset | `DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION` | 0x10E41DF3 | Override SR preset letter |
| FG preset | `DXVK_NVAPI_DRS_NGX_DLSS_FG_OVERRIDE_RENDER_PRESET_SELECTION` | 0x10E41DF1 | Override frame gen preset |
| SR scaling ratio | `DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE_SCALING_RATIO` | 0x10E41DF5 | Custom render scale |
| NR override | `DXVK_NVAPI_DRS_NGX_DLSS_NR_OVERRIDE` | — | Neural Rendering override |

---

## References

- `references/dota2-vulkan-launch-optimization.md` — Dota 2 Vulkan launch flags (`-vulkan -high -novid +@panorama_min_comp_layer_dimension 0 -prewarm_panorama`) that fix severe CPU/GPU imbalance, plus KWin `WindowsBlockCompositing` interplay and irqbalance enablement.

## Tips & Pitfalls

1. **`DXVK_NVAPI_DRS_SETTINGS` env var with commas may break** — Steam's launch option parser can eat commas. Use individual `DXVK_NVAPI_DRS_NGX_*` env vars instead. DXVK-NVAPI's `enrichwithenv()` picks them up.

2. **DLSS indicator overlay does NOT work on Linux** — `PROTON_DLSS_INDICATOR=1` writes registry keys for NGX debug logging, not a visible screen overlay. The visual green DLSS badge requires NVIDIA Profile Inspector (Windows-only).

3. **`PROTON_ENABLE_NVAPI=1` is unnecessary in GE-Proton11-1+** — NVAPI is auto-enabled via `DXVK_ENABLE_NVAPI=1` unless explicitly disabled. Only `PROTON_DISABLE_NVAPI=1` and `PROTON_FORCE_NVAPI=1` are recognized.

4. **Vulkan present mode `immediate` bypasses frame cap** — Setting this in MangoHud or globally makes `fps_limit` ineffective. Use `mailbox` for low latency + capped FPS.

5. **Goverlay writes `fps_limit=0` (unlimited)** — If the frame cap isn't working, check that the config file has a non-zero `fps_limit`. Goverlay's default is 0 = unlimited. Also check `vulkan_present_mode` isn't set to `immediate`.

6. **Shader cache is per driver version** — Upgrading NVIDIA driver invalidates all VKD3D pipeline caches. First session stutters. Let it rebuild naturally.
