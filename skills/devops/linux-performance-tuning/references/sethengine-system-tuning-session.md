# System Tuning Session — June 2026

## System
- **CPU**: Intel Core Ultra 7 265K (Arrow Lake) P 0-7 @5.4GHz, E 8-19 @4.6GHz
- **GPU**: NVIDIA RTX 5060 Ti 16GB, driver 595.71.05 (open modules)
- **MB**: Gigabyte Z890 AERO G
- **RAM**: 64GB DDR5
- **Monitor**: HP X34 3440x1440@165Hz DP
- **Audio**: ALC1220 → Douk Audio amp → Sony WH-1000XM3
- **Mouse**: Corsair KATAR PRO XT (flat accel)
- **Disk**: Kingston SA2000M8 1TB (boot), WD SN850X 2TB (data)

## Software
- Manjaro, kernel 7.0.10-1-MANJARO, KDE Plasma 6.6.5 Wayland
- NVIDIA open modules (linux70-nvidia-open 595.71.05-11)

## Kernel Command Line
```
preempt=full nohz_full=0-7 rcu_nocbs=0-7
cpufreq.default_governor=performance
nvidia_drm.modeset=1
intel_idle.max_cstate=4
usbhid.mousepoll=1 usbhid.kbpoll=1
pcie_aspm.policy=performance
intel_pstate=active sched_itmt_enabled=1
```

## Fixes Applied

### 1. Chrome WebGL/GeoGuessr Slow
**Cause**: `--use-gl=angle` without `--use-angle=vulkan` → ANGLE falls back to SwiftShader.

**Fix**: `~/.config/chrome-flags.conf`:
```
--ozone-platform=wayland
--use-gl=angle --use-angle=vulkan
--ignore-gpu-blocklist
--disable-gpu-driver-bug-workarounds
--enable-gpu-rasterization
--enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks
--num-raster-threads=10
```

### 2. IRQ Pinning — System Freezes
**Cause**: Old script pinned GPU IRQs to a single E-core (1.6M interrupts on core 8 only) with C3 wake latency (1048µs).

**Fix**: `/usr/local/bin/pin-irqs-dynamic` v4:
- GPU IRQs → E-cores 8-11 (4 cores, round-robin)
- USB IRQs → E-cores 12-13 (2 cores, separate from GPU)
- Background (NVMe/audio/WiFi/eth) → E-cores 14-19 (hex mask `fc000`)
- NVMe straggler catch: periodic re-pin via hex mask verification (`0x3F00` bitmask for GPU+USB zone)
- C2/C3 disabled on cores 8-13 via sysfs loop (`state_num="${state_dir##*state}"`)
- EPP=performance via `cpupower -c <cpu> set --epp performance`
- Performance governor on cores 8-13

**Bug fixed**: The `index` file in cpuidle state dirs doesn't exist on kernel 7.0+. Changed from `cat $state_dir/index` to `"${state_dir##*state}"`.

**Bug fixed**: EPP must be set via `cpupower -c <cpu> set --epp performance` — direct sysfs write fails when performance governor is already active.

### 3. DPMS Wake Black Screen
**Cause**: NVIDIA GSP firmware fails DisplayPort link training on HP X34 after display-off → wake.

**Fix**: `/etc/modprobe.d/nvidia-perf.conf`:
```
options nvidia NVreg_EnableGpuFirmware=0 NVreg_PreserveVideoMemoryAllocations=1
   NVreg_DynamicPowerManagement=0x02 NVreg_UsePageAttributeTable=1
   NVreg_RegistryDwords="RMIntrLockingMode=1;RMNvDecSurfacesPerContext=32"
   NVreg_EnableResizableBar=1
options nvidia_drm modeset=1 fbdev=1
```
Requires `sudo mkinitcpio -P && sudo reboot` for modprobe.d to take effect on Arch.

### 4. Auto-Suspend Disabled
Always: `~/.config/powermanagementprofilesrc` → `AutoSuspendIdleTimeoutSec=0`

### 5. scx_rustland Config
Fixed: `/usr/share/scx_loader/config.toml` — `default_mode = "Gaming"` (was lowercase "gaming", which crashed the loader).

### 6. Elisa / SystemSettings 100% CPU
**Cause**: Xwayland crash → Wayland apps lose connection → fall into "no outputs — placeholder screen" → infinite render loop for 15+ hours.

**Workaround**: `killall elisa systemsettings` if it happens again.

## IRQ Pinning Service
- Service: `/etc/systemd/system/pin-irqs-dynamic.service` (oneshot, triggered by timer)
- Timer: `/etc/systemd/system/pin-irqs-dynamic.timer` (OnBootSec=10, OnUnitActiveSec=6000)
- Log: `/var/log/irq-pinning.log`

## NVMe IRQ Affinity
NVMe driver (nvme.ko) overrides manual `/proc/irq/` affinity writes for MSI-X queue completion IRQs. The straggler catch in the script re-applies affinity on a timer. Some queues will inevitably drift to GPU/USB cores between timer runs — negligible impact (<5% of interrupt volume on those cores).

## GSP Status
`nvidia-smi --query-gpu=gsp.mode.current --format=csv,noheader` still shows "Enabled" until initramfs is rebuilt with the modprobe.d change.
