---
session: 20260502_174824_f53a50
date: 2026-05-02
category: system
tags: [corsair, mouse, hwdb, polling, udev, input]
---

# Corsair KATAR PRO XT Mouse Polling Rate Tuning

The Corsair KATAR PRO XT Gaming Mouse (USB VID:PID 1b1c:1bac) was tuned to 1000Hz polling which caused compositor issues on NVIDIA Wayland. Downgraded to 500Hz via udev hwdb:

File `/etc/udev/hwdb.d/71-corsair-polling.hwdb`:
```
evdev:input:b0003v1b1Cp1bac* MOUSE_POLL=2
```

The `MOUSE_POLL=2` sets 2ms interval (500Hz). Apply with:
```bash
sudo systemd-hwdb update && sudo udevadm trigger
```

Also set libinput acceleration to flat (no accel):
```bash
xinput set-prop "Corsair CORSAIR KATAR PRO XT Gaming Mouse" "libinput Accel Speed" 0
```

Other peripherals: BY Tech Thor 230 headset/keyboard (331a:5020), Gigabyte ITE device (048d:5711).

## References
- [[usbhid-low-latency-quirks]]
- [[nvidia-wayland-kwin-latency-policy]]
