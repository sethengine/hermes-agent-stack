# System Tuning Session — 2026-06-10

## System
- **CPU**: Intel Core Ultra 7 265K (20C, P-cores 0-7 @ 5.4 GHz, E-cores 8-19 @ 4.6 GHz)
- **GPU**: NVIDIA RTX 5060 Ti 16GB (driver 595.71.05, open kernel modules)
- **RAM**: 64 GB DDR5
- **Storage**: Kingston 1TB NVMe (boot/home) + WD SN850X 2TB NVMe (data)
- **Display**: HP X34 3440×1440 @ 165 Hz ultrawide (DisplayPort)
- **OS**: Manjaro Linux, kernel 7.0.10-1, KDE Plasma 6.6.5 + KWin 6.6.5 on Wayland

## Issues Found & Fixed

### 1. Chrome/WebGL Slow (GeoGuessr, Google Maps)
- **Cause**: `--use-gl=angle` in chrome-flags.conf without `--use-angle=vulkan` — ANGLE defaulted to SwiftShader (software) for WebGL on NVIDIA Wayland
- **Fix**: Add `--use-angle=vulkan` and `--disable-gpu-driver-bug-workarounds`

### 2. Heavy Input Latency
- **Cause**: Team Fortress 2 running in background (`tf_linux64 -vulkan`) using 81% CPU + 3.5 GB VRAM, keeping GPU at 2745 MHz / 80W. KWin compositor starved.
- **Fix**: Kill/suspend TF2 (`kill 380990`)

### 3. Display Wake Black Screen
- **Cause**: PowerDevil's DPMS monitoring broken on NVIDIA Wayland (`Watching for DPMS state changes unimplemented`). System tried to suspend after 1 hr → GSP firmware failed DisplayPort link training on wake.
- **Fixes applied**: `AutoSuspendIdleTimeoutSec=0` (never auto-suspend)
- **Pending fix**: `RMUseSwLinkTraining=1` via modprobe.d or `NVreg_EnableGpuFirmware=0`

### 4. System Freezes / "System Not Responding"
- **Root cause**: `pin-irqs-dynamic` script pinned ALL NVIDIA GPU IRQs to a single E-core (core 8) + USB to separate E-cores. 1.6M interrupts saturating one 4.6 GHz E-core → KWin compositor lockups.
- **Fix**: Rewrote script (v3) to:
  - GPU IRQs → E-cores 8-11 (round-robin across 4 cores)
  - USB IRQs → E-cores 12-13 (separate from GPU)
  - NVMe/Audio/WiFi/Ethernet → E-cores 14-19 (shared, can overlap)
  - C2 (127 µs) + C3 (1048 µs) disabled on GPU+USB cores (only C1 @ 1 µs remains)
  - Bug: script used `/sys/.../cpuidle/state*/index` which doesn't exist on this kernel. Fixed to extract index from directory name (`${state_dir##*state}`)

### 5. PowerDevil Crashes
- **Cause**: XDG portal registration fails (`App info not found for 'org.kde.org_kde_powerdevil'`). App ID string mangled in KDE 6 (sends `org.kde.org_kde_powerdevil` instead of `org.kde.powerdevil`).
- **Status**: Cosmetic only — PowerDevil runs fine despite the error.

### 6. Orphaned Inodes on /home
- **Cause**: Apps (dota2, Chrome) crashing without flushing filesystem. `/home` at 93% full.
- **Status**: Clean up disk space to reduce risk.

### 7. Broken Autostart Entry
- **Fix**: Moved `mouse-flat.sh` from `~/.config/autostart/` to `~/.local/bin/` and created proper `.desktop` file (`mouse-flat.desktop`) that KDE autostart recognizes.

### 8. scx_loader Failed at Boot
- **Cause**: Config typo — `default_mode = "gaming"` (lowercase) instead of `"Gaming"` in `/usr/share/scx_loader/config.toml`.
- **Fix**: Capitalised G. scx_rustland now set as default scheduler in Gaming mode.

## Key Locations
- `~/.config/chrome-flags.conf` — Chrome flags
- `/usr/local/bin/pin-irqs-dynamic` — IRQ pinning script (v3)
- `/etc/modprobe.d/nvidia-perf.conf` — NVIDIA module params
- `~/.config/powerdevilrc` — KDE power settings
- `~/.config/powermanagementprofilesrc` — KDE suspend settings
- `/usr/share/scx_loader/config.toml` — sched-ext loader config
- `~/.config/autostart/mouse-flat.desktop` — mouse acceleration fix
