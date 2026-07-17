# NVIDIA nvidia-open DRM Syncobj FD Leak — plasmashell Crash

## Summary

The `nvidia-open` kernel module leaks file descriptors through the Wayland `wp_linux_drm_syncobj_manager_v1.import_timeline` protocol. plasmashell crashes with "Too many open files" after 12-16 hours. The proprietary `nvidia` module does not have this leak.

## Affected Configuration

- **Driver**: nvidia-open (open kernel module, MIT/GPL license)
- **Driver versions tested**: 595.71.05
- **GPU**: RTX 5060 Ti (Blackwell, but likely affects all GPUs on nvidia-open + Wayland)
- **Compositor**: KWin Wayland (KDE Plasma 6)
- **Desktop**: plasmashell (KDE taskbar/shell)
- **Kernel**: 7.0.10-1-MANJARO
- **Display server**: Wayland

## Crash Trace

```
plasmashell[PID]: Error marshalling request for wp_linux_drm_syncobj_manager_v1.import_timeline: Too many open files
plasmashell[PID]: eglSwapBuffers failed with 0x3000, surface: 0x...
plasmashell[PID]: The Wayland connection experienced a fatal error: Too many open files
systemd: plasma-plasmashell.service: Main process exited, code=exited, status=255/EXCEPTION
systemd: plasma-plasmashell.service: Failed with result 'exit-code'.
systemd: plasma-plasmashell.service: Scheduled restart job, restart counter is at 1.
```

## Timeline for This System

| Crash # | Date | Uptime Before Crash | PID | Status After |
|---------|------|-------------------|-----|-------------|
| 1 | Jul 3, 23:44 | 16h12m | 1861 | Restarted as 656022 |
| 2 | Jul 4, 20:32 | 11h52m | 656022 | Restarted with LimitNOFILE fix |

## Leak Rate

After quick-fix restart with LimitNOFILE=65536:
- 5 seconds uptime: 168 FDs
- Estimated time to hit 65536: 20+ days

## Quick Fix (interim)

Raising `LimitNOFILE=65536` in the systemd user service override stops the crash for weeks. The leak is still active but takes much longer to hit the limit.

## Permanent Fix

Switch from `linux70-nvidia-open` to `linux70-nvidia` (proprietary module). The proprietary module uses a different DRM syncobj code path that does not leak FDs.

## Investigation Commands

```bash
# FD leak confirmation
journalctl -b --no-hostname | grep 'import_timeline: Too many open files'

# Current FD usage
ls /proc/$(pgrep -o plasmashell)/fd | wc -l

# FD limits
cat /proc/$(pgrep -o plasmashell)/limits | grep 'open files'

# Check if running open or proprietary module
modinfo -F license nvidia  # "Dual MIT/GPL" = open, "NVIDIA" = proprietary
lsmod | grep ^nvidia  # Check module name

# plasmashell crash/restart history
journalctl -b --no-hostname | grep 'plasma-plasmashell.service.*exit-code'
```

## Linked From

`software-development/nvidia-wayland-kde/SKILL.md` — Section "plasmashell Crash on NVIDIA Wayland: DRM Syncobj FD Leak"
