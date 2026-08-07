# HDR Gaming Setup — Dead Space Remake Case Study

**System:** Manjaro, KDE Plasma 6.6.5, NVIDIA 595.71.05, RTX 5060 Ti, 3440×1440@165Hz  
**Date:** 2026-07-04

## System State (verified working)

| Component | Detail |
|-----------|--------|
| Monitor | DP-3 (3440×1440), peak 400 nits |
| KDE HDR | Enabled via `kscreen-doctor output.DP-3.hdr.enable` |
| gamescope | 3.16.24-1 |
| Proton | GE-Proton11-1 (installed in `~/.local/share/Steam/compatibilitytools.d/`) |
| Steam library | `~/.local/share/Steam` |
| Game App ID | 1693980 (Dead Space Remake) |

## Known-Working Launch Options

**Standard (HDR + VRR):**
```
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- %command%
```

**With HDR force + NVAPI (if game doesn't detect HDR):**
```
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- env PROTON_ENABLE_NVAPI=1 PROTON_HIDE_NVIDIA_GPU=0 VKD3D_CONFIG=hdr %command%
```

**Fallback — no VRR (for black screen on launch):**
```
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --steam -- %command%
```

## Pitfalls

- Steam launch options with `%command%` require proper quoting. The `--` before `env` is critical — it separates gamescope args from the child process args.
- `DXVK_HDR=1` does NOT work for DX12 games (Dead Space Remake is DX12). Use `VKD3D_CONFIG=hdr`.
- KDE may lose HDR state after sleep/resume. Re-run `kscreen-doctor output.DP-3.hdr.enable`.
- The game must be installed before launch options take effect.
- Setting Proton compat layer in Steam Properties → Compatibility is required even though GE-Proton exists in the compat tools directory — Steam won't auto-detect it.

## Verification Commands

```bash
# Check HDR state
kscreen-doctor -o | grep HDR

# Check gamescope running with HDR
cat /proc/$(pidof gamescope)/cmdline | tr '\0' ' '

# Check NVIDIA driver
nvidia-smi --query-gpu=driver_version --format=csv,noheader

# Check gamescope version
gamescope --version

# Install game via Steam (if not installed)
steam steam://install/1693980
```
