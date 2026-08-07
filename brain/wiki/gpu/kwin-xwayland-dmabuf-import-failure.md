---
source_session: 20260802_145101_071791
category: gpu
date: 2026-08-04
tags: [kwin, xwayland, dmabuf, nvidia, wayland, error-signature, broken-windows]
---

# XWayland dmabuf Import Failure: Error Signature for Broken Windows (NVIDIA Wayland)

## Symptom
KWin Wayland session with only ~3 GUI windows and errors; X11 clients (Firefox, etc.) fail to appear. Root cause is NOT `Backend=O` in kwinrc (KWin 6.7.3 ignores `Backend=` — log says `No backend specified, automatically choosing drm`).

## The smoking-gun error (journal)
```
kwin_wayland_wrapper: XWAYLAND: [destroyed object]: error 7: importing the supplied dmabufs failed
kwin_wayland_wrapper: (EE) failed to dispatch Wayland events: Protocol error
```
XWayland can't import dmabufs from the compositor → kills X11 clients. This is the signature to grep for when Windows/panels disappear on NVIDIA Wayland.

## Stale compose/triple-buffer vars are mostly no-ops on KWin 6
Cleanup of `KWIN_COMPOSE=O2`, `KWIN_TRIPLE_BUFFER=0`, `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1` (from `~/.config/plasma-workspace/env/*.sh` and `~/.config/environment.d/99-kwin.conf`) tidies config but does NOT fix dmabuf breakage:
- `KWIN_COMPOSE=O2` — ignored by KWin 6.7.3 Wayland (auto DRM backend)
- `KWIN_TRIPLE_BUFFER=0` — KDE5 relic, no-op on KDE6
- `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1` — real but only affects NVIDIA smoothness, not stability

## Also verified
- `nvidia_drm.modeset=1` already active in `/proc/cmdline` and `/etc/modprobe.d/nvidia.conf` (grep with `_`, not `-` — hyphen grep misses it).
- Check journal for dmabuf protocol errors first; don't chase dead env vars.

## Related
- [[kwin-latency-compositor]]
- [[kwin-compose-values-landmine]]
- [[kwin-systemd-environment-vars]]
