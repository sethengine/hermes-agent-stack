---
source: session 20260609_195359_ab296b (Keyboard Input Latency Investigation)
date: 2026-06-09
category: kernel/
---

# Pinning USB IRQ to P-Cores

The USB controller (xhci_hcd) IRQ for input devices can land on E-cores, which have lower frequency and higher latency than P-cores.

## How to Check

```sh
# Find the USB IRQ number for xhci_hcd
grep xhci_hcd /proc/interrupts
# Check which CPU(s) it's affined to
cat /proc/irq/<N>/smp_affinity_list
```

## Permanent Fix via systemd

Create `/etc/systemd/system/pin-usb-irq.service`:

```systemd
[Unit]
Description=Pin USB keyboard IRQ to P-core
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 2 > /proc/irq/138/smp_affinity_list'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Then `sudo systemctl daemon-reload && sudo systemctl enable --now pin-usb-irq`.

For Arrow Lake (Ultra 7 265K): P-cores are 0-7, E-cores are 12-19. Pinning to CPU 2 places it within the "USB on P-cores 2-3" zone used in previous latency tuning.

See also: [[usb-input-autosuspend-disable]]
