# NVIDIA Hybrid GPU Environment Variables for Intel Arrow Lake

**source:** session `20260606_165853_59306d` (2026-06-06, updated 2026-07-12)
**category:** software
**tags:** [nvidia, intel, arrow-lake, hybrid-gpu, wayland, environment-variables, libva]

## Configuration

On an Intel Core Ultra 7 265K (Arrow Lake) with integrated Xe graphics + NVIDIA GeForce RTX 5060 Ti on Wayland, the correct environment variables for optimal performance and low latency:

```bash
# Primary GPU offload variable
export __NV_PRIME_RENDER_OFFLOAD=1

# VA-API video decode goes through NVIDIA
export LIBVA_DRIVER_NAME=nvidia

# Direct NVIDIA backend (avoids EGL intermediates)
export NVD_BACKEND=direct
```

These are typically set in `~/.profile` or per-application desktop files.

## Key Points

- `LIBVA_DRIVER_NAME=nvidia` should be set **globally** (both `~/.profile` and any per-application config files).
- `NVD_BACKEND=direct` avoids extra EGL proxy layer — improves decode latency.
- For hybrid setups, the NVIDIA GPU should handle rendering via the proprietary driver while Intel Xe handles display.
- Some applications (Chrome, Firefox) need these in their `.desktop` file `Exec` line rather than global environment.
