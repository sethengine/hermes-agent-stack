# XWayland dmabuf import failure + nvidia_drm.modeset verification (KWin 6.7.3)

Session-specific transcript detail backing the SKILL.md pitfall section.

## Symptom (user report)
- "kwin is not running well, no gui, just 3 windows and errors"
- Only some (X11/XWayland) windows present; compositor up but X11 clients failing.

## Journal evidence (the real signal)
```
kwin_wayland_wrapper[4170]: XWAYLAND: [destroyed object]: error 7: importing the supplied dmabufs failed
kwin_wayland_wrapper[4170]: (EE) failed to dispatch Wayland events: Protocol error
kwin_wayland_wrapper[2973]: error in client communication (pid 2973)
kwin_wayland[2973]: No backend specified, automatically choosing drm
```
Also harmless noise that appears in the same log and should NOT be chased:
- `kwin_wayland[2973]: Failed to register with host portal ... Unable to open /proc/2973/root` — portal/sandbox quirk, does not affect rendering.
- `xkbcomp: Warning ... Unsupported maximum keycode 709` — keyd/keyboard map, not fatal.
- A `python3[11327]: FAILED KWin segfault in VulkanDevice ... Traceback` line was from an **agent/LLM tool log running as a python process**, NOT a real KWin crash. Genuine KWin crashes appear under the kwin_wayland / kwin_wayland_wrapper units with a backtrace. On Wayland `~/.xsession-errors` is usually empty (everything goes to journald) — do not treat emptiness as "no logs".

## Verified facts (commands, not journal)
- kwin_wayland --version => kwin 6.7.3
- nvidia-smi driver_version => 610.43.03
- /dev/dri has card0 + renderD128
- /proc/cmdline => nvidia_drm.modeset=1  (ALREADY ACTIVE)
- /etc/modprobe.d/nvidia.conf line: options nvidia_drm modeset=1 fbdev=1 color_pipeline=1

## The grep gotcha (mistake made this session)
`tr ' ' '\n' < /proc/cmdline | grep -oE 'nvidia-drm...'` (hyphen) returned nothing → wrong initial theory "modeset off". The parameter is `nvidia_drm` with an **underscore**. Cross-check both the hyphenated and underscored forms; `/proc/cmdline` is the live source of truth (grub.cfg can be stale).

## Triage / remaining suspects (since modeset is already =1)
1. color_pipeline=1 on nvidia_drm — new NVIDIA color API; known to break dmabuf import with KWin 6.7.x across some 600-series configs. Needs REBOOT to change (module already loaded).
2. Explicit-sync (linux-drm-syncobj) handshake KWin<->driver — test with `KWIN_DRM_DISABLE_EXPLICIT_SYNC=1` in ~/.config/environment.d/; only needs logout/login, not reboot.
3. Scope check: if only XWayland/X11 apps break while Wayland-native apps are fine => XWayland dmabuf path, not compositor crash.

## Non-skill config locations searched this session
- KWIN_COMPOSE / KWIN_TRIPLE_BUFFER / KWIN_DRM_DISABLE_TRIPLE_BUFFERING lived in:
  - ~/.config/plasma-workspace/env/kwin.sh
  - ~/.config/plasma-workspace/env/kwin-performance.sh
  - ~/.config/environment.d/99-kwin.conf
- kwinrc [Compositing] Backend=O => ignored; KWin 6.7.3 Wayland auto-selects drm in mode (log: "No backend configured, automatically choosing drm").
- Removing the stale compose/triple-buffer vars is hygiene, not the dmabuf fix. With modeset already on, do not re-add nvidia-drm.modeset to GRUB / nvidia.conf (duplicate no-op).