---
source_session: "20260703_202938_ecafcd"
date: "2026-07-03"
category: software
tags: [dead-space-remake, proton, nvidia, directx-error, low-latency-layer, gaming]
---

# Dead Space Remake DirectX Crash on Proton (NVIDIA)

**Symptom:** "DirectX Error" / "GPUBreadcrumbs" crash with NVIDIA driver 595.71 on Dead Space Remake (2023) when using Proton launch flags.

**Root cause:** Conflict between `VK_INSTANCE_LAYERS=VK_LAYER_low_latency_layer` and the NVIDIA driver's **native Reflex** (enabled by `PROTON_ENABLE_NVAPI=1`). On NVIDIA GPUs that support Reflex natively (RTX 30/40/50 series), the low_latency_layer Vulkan layer intercepts the same Reflex calls the driver handles, causing GPU state inconsistency → TDR/driver crash.

**Fix:**
1. Strip to `gamemoderun mangohud %command%` (no special flags)
2. Use only `PROTON_ENABLE_NVAPI=1 DXVK_NVAPI_ALLOW_OTHER_DRIVERS=1` for latancy — omit `VK_INSTANCE_LAYERS`
3. `PROTON_DLSS_UPGRADE=1` is **CachyOS-Proton only** and unsafe on standard Proton
4. Clear caches after changing flags:
   ```bash
   rm -rf ~/.steam/steamapps/compatdata/1693980/
   rm -rf ~/.steam/steamapps/shadercache/1693980/
   rm -rf ~/.cache/dxvk/
   ```

**Prevention:** low_latency_layer should be excluded for games on RTX 30/40/50 series that use `PROTON_ENABLE_NVAPI=1`. The native driver Reflex is sufficient.

[[low-latency-layer]] [[nvidia-reflex]] [[proton-troubleshooting]] [[keyd]]
