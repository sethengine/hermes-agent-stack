---
source: 20260502_150358_5e17d2
category: system
date: 2026-07-06
tags: [mouse, acceleration, flat, libinput, wayland, kde, kwin, dbus]
---

# Mouse Acceleration: Flat Profile on Wayland KDE

On Wayland, `xinput` does NOT work — libinput acceleration must be controlled through KDE per-device config or DBus.

## KDE Per-Device Config (persistent)

Edit `~/.config/kcminputrc`:
```ini
[Libinput][6940][7084][Corsair CORSAIR KATAR PRO XT Gaming Mouse]
PointerAcceleration=0
PointerAccelerationProfile=0
```
Profile `0` = flat, `1` = adaptive. Requires logout/login to apply.

## DBus Runtime (immediate)

```bash
dbus-send --session --dest=org.kde.KWin --type=method_call \
  /org/kde/KWin/InputDevice/event3 \
  org.kde.KWin.InputDevice.pointerAccelerationProfileFlat
```

## Verification

```bash
dbus-send --session --dest=org.kde.KWin --type=method_call \
  /org/kde/KWin/InputDevice/event3 \
  org.freedesktop.DBus.Properties.Get \
  string:org.kde.KWin.InputDevice string:pointerAcceleration
# Returns 0.0 = flat confirmed
```

## References
- [[corsair-katar-pro-xt-config]]
- [[nvidia-wayland-display-color-after-sleep]]
