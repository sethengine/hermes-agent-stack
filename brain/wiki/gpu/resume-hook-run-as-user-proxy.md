---
source_session: 20260711_133313_2ff88a
category: gpu
date: 2026-07-31
tags: [resume, sleep, kscreen-doctor, runuser, wayland, systemd-sleep, hook]
---

# Resume Hook Must Run Display Commands as User (run_as_user proxy)

## Problem

The systemd sleep hook `/usr/lib/systemd/system-sleep/latency-fix` runs as **root**, but display commands like `kscreen-doctor` need the user's Wayland session environment (Qt platform plugin, `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`). Without it they crash:

```
kscreen-doctor: This application failed to start because no Qt platform plugin could be initialized. Aborted (core dumped)
```

Every `kscreen-doctor` call in the hook died on resume — the display never came back.

## Fix — runuser proxy

Wrap display commands in a `run_as_user` function inside the hook:

```bash
run_as_user() {
    runuser -u sethengine -- env \
        DISPLAY=:0 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 \
        QT_QPA_PLATFORM=wayland "$@"
}
run_as_user kscreen-doctor output.DP-3.disable
sleep 2
run_as_user kscreen-doctor output.DP-3.enable
```

## Also: use `qdbus6`, not `qdbus`

`qdbus` only exists at `/usr/lib/qt6/bin/qdbus` — not on root's PATH in the hook. `qdbus6` is at `/usr/bin/qdbus6` and works. The hook must call `qdbus6 org.kde.KWin /Compositor active` (returns `true` when compositor is up).

## Verification

- `runuser` as root ✅
- `kscreen-doctor` with session env sees full mode list, exit 0 ✅
- `qdbus6 ... /Compositor active` → `true` ✅

## Related

- [[resume-hook-dp-toggle]] — the DP toggle this proxy wraps
- [[post-sleep-optimization-verification]]
- [[nvidia-edid-fake-nvd-after-sleep]]
