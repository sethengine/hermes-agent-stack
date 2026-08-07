---
source: session 20260609_195359_ab296b (Keyboard Input Latency Investigation)
date: 2026-06-09
category: kernel/
---

# Disabling USB Autosuspend for Input Devices

USB autosuspend causes input devices (keyboard, mouse) to enter low-power states, introducing latency when they wake to process input.

## Permanent Fix via udev Rules

Create a udev rule file (`/etc/udev/rules.d/90-usb-input-noautosuspend.rules`) with entries per device:

```udev
# BY Tech Thor 230 keyboard - disable autosuspend
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="331a", ATTRS{idProduct}=="5020", ATTR{power/autosuspend}="-1"

# Corsair KATAR PRO XT mouse - disable autosuspend
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", ATTRS{idProduct}=="1bac", ATTR{power/autosuspend}="-1"
```

Apply with:

```sh
sudo udevadm control --reload-rules
sudo udevadm trigger -v -s usb -a idVendor=1b1c -a idProduct=1bac
```

Find device vendor/product IDs via `lsusb` or `udevadm info -a -n /dev/input/by-path/...`.
