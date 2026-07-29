# NVIDIA Wayland Environment Variables

## System-wide config
File: `/etc/environment.d/99-nvidia-wayland.conf`

```ini
WLR_NO_HARDWARE_CURSORS=1          # REQUIRED — eliminates cursor stutter on NVIDIA Wayland
GBM_BACKEND=nvidia-drm             # Native GBM backend (vs EGLStreams)
__GL_SYNC_TO_VBLANK=0              # Disable forced VSync in GL apps
__GLX_VENDOR_LIBRARY_NAME=nvidia   # Force NVIDIA GLX
QT_QPA_PLATFORM=wayland            # Qt apps use native Wayland (KDE)
XDG_SESSION_TYPE=wayland           # Inform apps we're on Wayland
```

## Per-user (terminal-only — add to ~/.zshrc)
```bash
export WLR_NO_HARDWARE_CURSORS=1
export GBM_BACKEND=nvidia-drm
export __GL_SYNC_TO_VBLANK=0
```

## Notes
- `/etc/environment.d/` applies to ALL apps (systemd user manager picks it up) — Firefox, VSCode, Chromium, etc.
- `~/.zshrc` only covers terminal-launched apps. Systemd-launched (KDE autostart, desktop files) won't see them.
- `WLR_NO_HARDWARE_CURSORS=1` is critical for NVIDIA Wayland. Without it, the hardware cursor plane on NVIDIA causes visible stutter and occasional 1-frame lag spikes.
- `nvidia-settings -a '[gpu:0]/GPUPowerMizerMode=1'` requires the NV-CONTROL X extension which is NOT available on pure Wayland. The command silently fails. Use `nvidia-smi -pm 1` instead for persistence mode.
- **Detected vs Set PowerMizer**: Run `nvidia-settings -t -q GPUPowerMizerMode` — returns 0 (Auto) on Wayland regardless. The driver manages P-states automatically based on 3D load.

## Verifying env vars took effect
```bash
cat /proc/$(pidof firefox)/environ 2>/dev/null | tr '\0' '\n' | grep WLR
cat /proc/$(pidof kwin_wayland)/environ 2>/dev/null | tr '\0' '\n' | grep WLR
```
