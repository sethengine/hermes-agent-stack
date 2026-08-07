---
session: 20260502_174824_f53a50
date: 2026-05-02
category: kernel
tags: [usbhid, quirks, latency, input, grub, corsair, hid]
---

# USB HID Low-Latency Quirks via Kernel Cmdline

USB HID devices can be tuned for lower latency by passing `usbhid.quirks=VID:PID:0x40` in the kernel cmdline. The `0x40` quirk enables low-latency HID raw mode (1ms polling, no processing delay). Also add `usbcore.autosuspend=-1` to prevent USB sleep.

For a Corsair KATAR PRO XT (1b1c:1bac) and BY Tech Thor 230 (331a:5020) on Arrow Lake system:

```
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40 usbcore.autosuspend=-1
```

Added to `/etc/default/grub` GRUB_CMDLINE_LINUX_DEFAULT then `sudo grub-mkconfig -o /boot/grub/grub.cfg` + reboot. The existing `usbhid.mousepoll=1` and `usbhid.kbpoll=1` were already set for 1ms polling.

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[corsair-katar-pro-xt-config]]
