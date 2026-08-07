---
source: "20260711_190829_979025,20260502_150358_5e17d2"
category: system
date: 2026-07-11
tags: [libinput, mouse, acceleration, flat, udev, wayland]
---

# Setting libinput Default Acceleration Profile via udev

The `*` prefix in `libinput list-devices` shows the compile-time default acceleration profile. To change what's marked as default (not just runtime override), use a udev property.

## udev Rule

Create `/etc/udev/rules.d/99-mouse-accel-flat.rules`:

```bash
ACTION=="add|change", SUBSYSTEM=="input", ATTRS{idVendor}=="6940", ATTRS{idProduct}=="7084", ENV{LIBINPUT_ATTR_ACCEL_PROFILE}="flat"
```

Then reload udev:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

After replug or logout, `libinput list-devices` will show `*flat` as the default.

## How It Differs From KDE Config

The existing KDE/DBus approach (`~/.config/kcminputrc`, `pointerAccelerationProfileFlat`) overrides at the compositor level. The udev approach changes the **system default** that libinput reports — more fundamental but both achieve the same runtime result on Wayland KDE.

## Alternative: libinput local-overrides.quirks (2026-07-31)

Simpler per-device alternative to udev rules — `/etc/libinput/local-overrides.quirks` (no udev reload needed, just replug):

```ini
[Katar Pro]
MatchName=CORSAIR CORSAIR KATAR PRO XT Gaming Mouse*
AccelProfile=Flat

[Thor 230]
MatchName=BY Tech Thor 230*
AccelProfile=Flat
```

Verify after replug/relogin: `libinput list-devices 2>/dev/null | grep -A2 'Katar\|Thor' | grep Accel` → `*flat*`.

## References
- [[mouse-acceleration-flat-wayland-kde]]
- [[corsair-katar-pro-xt-config]]
