# DLSS DLL Replacement in GE-Proton

**Source Session:** `20260706_194614_c828c3` (Diablo 2 Wayland Nvidia Settings)
**Date:** 2026-07-08
**Category:** gpu

## Deprecated: PROTON_DLSS_UPGRADE=1

This env var was a Proton 9-era feature that auto-replaced `nvngx_dlss.dll` with a newer bundled version. Deprecated in Proton 10+. GE-Proton11-1 registers the flag in compat_config but the implementation was removed.

The replacement path in GE-Proton11-1 is OptiScaler (`PROTON_USE_OPTISCALER=1`), but OptiScaler is **not embedded** in the proton build - it's a flag with no backing code.

## Current Fix: Direct DLL Replacement

Replace `nvngx_dlss.dll` directly in the game's installation directory. DLSS 310.7.0.0 is the latest (confirmed against 135 entries in the NVIDIA manifest).

The GE-Proton `protonfixes/upscalers.py` code still exists and could handle this automatically, but it's no longer called by the current build.

## Automation

Launch option script + weekly cron:
```
/home/sethengine/.local/bin/d2r-dlss-update && mangohud %command%
```

The updater script checks the NVIDIA manifest, downloads the latest `nvngx_dlss.dll`, and drops it into the game directory before each launch.
