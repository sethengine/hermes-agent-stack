---
name: linux-input-latency-tuning
description: Complete system latency tuning for Linux desktop – Gigabyte Z890, Intel Arrow Lake, NVIDIA Wayland KDE. Covers GRUB, KWin, USB hwdb, sysctl, C-states, hugepages, NVIDIA env, resume hook, THP.
---

# Linux Input Latency Tuning

## Applicable Systems
- Gigabyte Z890 / similar Intel desktop
- NVIDIA RTX 5060 Ti (driver 580+)
- KDE Plasma 6 Wayland
- Manjaro / Arch Linux

## GRUB Kernel Parameters
Add to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then `sudo grub-mkconfig -o /boot/grub/grub.cfg`:

```
preempt=full threadirqs
cpufreq.default_governor=performance intel_pstate=active
usbhid.mousepoll=1 usbhid.kbpoll=1
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40
usbcore.autosuspend=-1
intel_idle.max_cstate=1 processor.max_cstate=1
hugepagesz=2M hugepages=2048
transparent_hugepage=madvise
pcie_aspm.policy=performance pci=pcie_bus_perf pcie_ports=native
vdso=2 skew_tick=1 futex_waitv=1
workqueue.power_efficient=false
nvidia_drm.modeset=1 nvidia_drm.fbdev=1
```

## USB hwdb 1000Hz
File: `/etc/udev/hwdb.d/71-corsair-polling.hwdb`
```
evdev:input:b*v1B1Cp1BAC* MOUSE_POLL=1
evdev:input:b*v331Ap5020* MOUSE_POLL=1
```
`sudo systemd-hwdb update && sudo udevadm trigger`

## Sysctl
File: `/etc/sysctl.d/99-workstation.conf`
```
vm.swappiness = 5
vm.dirty_ratio = 5
vm.dirty_background_ratio = 2
vm.page-cluster = 0
kernel.hung_task_timeout_secs = 0
kernel.sched_rt_runtime_us = -1
```

## KWin
File: `~/.config/kwinrc` → `[Compositing]`
```
Enabled=false
LatencyPolicy=LatencyLow
AnimationSpeed=0
MaxFps=165
GLVSync=never
```

## System-wide NVIDIA Env
File: `/etc/environment.d/99-nvidia-wayland.conf`
```
WLR_NO_HARDWARE_CURSORS=1
GBM_BACKEND=nvidia-drm
__GL_SYNC_TO_VBLANK=0
__GLX_VENDOR_LIBRARY_NAME=nvidia
QT_QPA_PLATFORM=wayland
XDG_SESSION_TYPE=wayland
```

## Resume Hook (CRITICAL: arg order)
File: `/usr/lib/systemd/system-sleep/latency-fix`
```
case "$1" in  # ← First arg = phase (pre/post), NOT $2 (suspend type)
    post)
        sleep 2
        udevadm trigger --subsystem-match=input --subsystem-match=usb
        udevadm settle --timeout=3
        # NVIDIA
        nvidia-settings -a '[gpu:0]/GPUPowerMizerMode=1' || true
        nvidia-smi -pm 1 || true
        # CPU
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo performance > "$cpu" || true
        done
        # Sysctl
        sysctl -w vm.swappiness=5 vm.dirty_ratio=5 kernel.sched_rt_runtime_us=-1 || true
        # Hugepages (compact first)
        echo 1 > /proc/sys/vm/compact_memory || true
        sleep 1
        for pages in 512 1024 1536 2048; do
            echo "$pages" > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null \
                && grep -q "HugePages_Total:.*$pages" /proc/meminfo && break || true
        done
        # KWin restart
        qdbus org.kde.KWin /Compositor suspend || true
        sleep 0.5
        qdbus org.kde.KWin /Compositor resume || true
    ;;
esac
```

## Disable Power Profiles Daemon
`sudo systemctl disable --now power-profiles-daemon`

## Chrome on NVIDIA Wayland
Use native EGL instead of ANGLE for lower latency:
`google-chrome-stable --use-gl=egl --ozone-platform=wayland`

## Known Issues
- `intel_idle/max_cstate` sysfs not available on kernel 7.0 — use GRUB `processor.max_cstate=1` instead
- NVIDIA PowerMizer=1 cannot be forced on pure Wayland (no X NV-CONTROL extension)
- Hugepages may not re-allocate to 2048 after S3 sleep if memory fragmented — hook falls back gracefully