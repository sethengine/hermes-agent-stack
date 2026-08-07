---
session: 20260502_174824_f53a50
date: 2026-05-02
category: system
tags: [keyd, keyboard, latency, input, virtual, systemd]
---

# keyd Virtual Keyboard Layer Adds Input Delay

The `keyd` service creates a virtual keyboard layer via `/dev/uinput` that adds measurable input delay. For a low-latency workstation, disabling it recovers raw hardware input:

```bash
systemctl --user stop --now keyd
systemctl --user mask keyd
```

To revert: `systemctl --user unmask keyd && systemctl --user start keyd`.

keyd was being used for keyboard remapping on the BY Tech Thor 230 headset keyboard. The virtual uinput device introduces a software processing layer (~5-10ms additional latency). Without keyd, the `usbhid.quirks=0x40` raw HID mode delivers events directly at 1ms polling.

## References
- [[usbhid-low-latency-quirks]]
- [[corsair-katar-pro-xt-config]]
