# System Tuning Session — June 2026

## Hardware
- **CPU**: Intel Core Ultra 7 265K (Arrow Lake) — P-cores 0-7 (5.4GHz), E-cores 8-19 (4.6GHz)
- **GPU**: NVIDIA RTX 5060 Ti 16GB (driver 595.71.05)
- **MB**: Gigabyte Z890 AERO G
- **RAM**: 64GB DDR5
- **Monitor**: HP X34 3440x1440@165Hz via DP
- **Mouse**: Corsair KATAR PRO XT (flat accel)
- **Disk**: WD SN850X 2TB + Kingston SA2000M8 1TB
- **Audio**: ALC1220 → Douk Audio amp → Sony WH-1000XM3

## Software
- **OS**: Manjaro Linux (rolling), kernel 7.0.10-1-MANJARO
- **DE**: KDE Plasma 6.6.5, Wayland, KWin 6.6.5
- **NVIDIA driver**: 595.71.05 (open kernel modules)
- **Chrome/Chromium**: 149.0.7827.53

## Kernel Parameters (cmdline)
```
preempt=full nohz_full=0-7 rcu_nocbs=0-7
cpufreq.default_governor=performance
nvidia_drm.modeset=1
intel_idle.max_cstate=4
usbhid.mousepoll=1 usbhid.kbpoll=1
pcie_aspm.policy=performance
intel_pstate=active sched_itmt_enabled=1
```

# Issues Found & Fixed

## 1. Chrome WebGL/GeoGuessr Slow + GPU Context Fails
**Root cause**: `~/.config/chrome-flags.conf` had `--use-gl=angle` without `--use-angle=vulkan`, causing ANGLE to fall back to SwiftShader (software) for WebGL on NVIDIA Wayland. Also had `--enable-native-gpu-memory-buffers` (known to break NVIDIA Wayland). Missing `--disable-gpu-driver-bug-workarounds`.

**Fix**:
```ini
--ozone-platform=wayland
--use-gl=angle
--use-angle=vulkan
--ignore-gpu-blocklist
--disable-gpu-driver-bug-workarounds
--enable-gpu-rasterization
--enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks
--num-raster-threads=10
```

## 2. Heavy Input Latency / Mouse Lag
**Root cause**: TF2 (Vulkan) running in background at 81% CPU + 3.5GB VRAM. GPU kept at 2745 MHz / 80W, saturating interrupt handling.

**Fix**: Kill TF2. Long-term: IRQ pinning (see below).

## 3. Monitor Black Screen on DPMS Wake
**Root cause**: NVIDIA GSP firmware fails DisplayPort link training on HP X34 after display sleep/blanking. Known bug in 595.xx driver series (Bug #2: Wayland OpenGL Black Screen After Resume, Bug #11: GSP Crash Xid 120).

**Fix**: Disable GSP firmware + preserve video memory:
```ini
# /etc/modprobe.d/nvidia-perf.conf
options nvidia NVreg_EnableGpuFirmware=0 NVreg_PreserveVideoMemoryAllocations=1
   NVreg_DynamicPowerManagement=0x02 NVreg_UsePageAttributeTable=1
   NVreg_RegistryDwords="RMIntrLockingMode=1;RMNvDecSurfacesPerContext=32"
   NVreg_EnableResizableBar=1
options nvidia_drm modeset=1 fbdev=1
```
Requires reboot.

## 4. System Freezes / Crashes (IRQ Saturation)
**Root cause**: Original script pinned NVIDIA GPU IRQs to E-core 8 only — **1.6M interrupts on one E-core** with C3 wake latency of 1048µs. When GPU loaded (TF2/Dota), IRQ saturates the E-core → KWin can't compose → desktop freezes.

**Fix**: Rewrote `/usr/local/bin/pin-irqs-dynamic` (v3):
- GPU IRQs → E-cores 8-11 (4 cores, round-robin)
- USB IRQs → E-cores 12-13 (2 cores, separate from GPU)
- NVMe/Audio/WiFi/Ethernet → E-cores 14-19 (shared)
- C2 (127µs) and C3 (1048µs) disabled on cores 8-13, only C1 (1µs) remains
- P-cores 0-7 untouched for foreground apps
- Bug fix: `state_idx` from non-existent `index` file → `state_num="${state_dir##*state}"` from directory name

## 5. PowerDevil Crashing in Loop
**Root cause**: XDG desktop portal couldn't register PowerDevil's app ID (`org.kde.org_kde_powerdevil` vs real `org.kde.powerdevil`). KDE 6 bug. Cosmetic — PowerDevil functions fine.

**Fix**: Not fixable without KDE patch. Symptom was mitigated by disabling auto-suspend.

## 6. System Auto-Suspending → Display Wake Failure
**Root cause**: `IgnoreIdleInhibitors=true` in powerdevilrc + `AutoSuspendIdleTimeoutSec=3600` → system tries S3 suspend after 1h regardless of Steam/Chrome blockers. NVIDIA Wayland suspend/resume path broken.

**Fix**:
```ini
# ~/.config/powermanagementprofilesrc
[AC][SuspendAndShutdown]
AutoSuspendIdleTimeoutSec=0
```

## 7. Elisa / System Settings 100% CPU for 15 Hours
**Root cause**: Xwayland crashed at 07:48 (broken pipe). All Wayland-connected apps lost connection. Most recovered, but Elisa and SystemSettings fell into "no outputs — creating placeholder screen" → infinite render loop at 100% CPU.

**Workaround**: `killall elisa systemsettings` if it happens again.

## 8. Dota2 + Chrome SIGSEGV Crashing + Xid Errors
**Root cause**: Xid 13 (Graphics Exception) and Xid 32 (Channel timeout) from dota2. Likely VRAM exhaustion (3.5GB for dota2) combined with IRQ-saturated E-cores. Separate from GSP issues.

**Fix**: IRQ pinning (prevents GPU channel timeouts by keeping interrupts responsive). GSP firmware disable also prevents GSP crash interactions.

## 9. scx_loader Failed at Boot
**Root cause**: Config file had `default_mode = "gaming"` (lowercase `g`), expected `"Gaming"` (capital G).

**Fix**: 
```toml
# /usr/share/scx_loader/config.toml
default_sched = "scx_rustland"
default_mode = "Gaming"
```

# Remaining Config Files

## ~/.config/chrome-flags.conf
```ini
--ozone-platform=wayland
--use-gl=angle --use-angle=vulkan
--ignore-gpu-blocklist
--disable-gpu-driver-bug-workarounds
--enable-gpu-rasterization
--enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks
--num-raster-threads=10
```

## /etc/modprobe.d/nvidia-perf.conf (pending reboot)
```ini
options nvidia NVreg_EnableGpuFirmware=0 NVreg_PreserveVideoMemoryAllocations=1
   NVreg_DynamicPowerManagement=0x02 NVreg_UsePageAttributeTable=1
   NVreg_RegistryDwords="RMIntrLockingMode=1;RMNvDecSurfacesPerContext=32"
   NVreg_EnableResizableBar=1
options nvidia_drm modeset=1 fbdev=1
```

## ~/.config/powerdevilrc
```ini
[AC][Display]
DimDisplayIdleTimeoutSec=0
TurnOffDisplayIdleTimeoutSec=0
```

## ~/.config/powermanagementprofilesrc
```ini
[AC][SuspendAndShutdown]
AutoSuspendIdleTimeoutSec=0
```

## /usr/local/bin/pin-irqs-dynamic (v3)
- GPU IRQs → E-cores 8-11
- USB IRQs → E-cores 12-13
- Background (NVMe/Audio/WiFi/Ethernet) → E-cores 14-19
- C2/C3 disabled on cores 8-13

# Things NOT Investigated
- Display dimming (started after powerdevil restart, reverted)
- Audio coil whine from GPU (known hardware issue)
