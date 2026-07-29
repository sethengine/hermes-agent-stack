# Per-IRQ Pinning to P-Cores via systemd Oneshot

USB controller (xhci_hcd) IRQs can land on E-cores, which have lower frequency and higher latency. Moving them to P-cores reduces input latency.

## Finding the IRQ Number

```bash
# Find xhci_hcd IRQ — look for USB controller lines
grep xhci_hcd /proc/interrupts

# Check which CPU it's currently affined to
cat /proc/irq/<N>/smp_affinity_list
```

On Intel Arrow Lake (Ultra 7 265K): P-cores are 0-7, E-cores are 12-19.

## Permanent Fix via systemd

Create `/etc/systemd/system/pin-usb-irq.service`:

```systemd
[Unit]
Description=Pin USB keyboard IRQ to P-core
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 2 > /proc/irq/<N>/smp_affinity_list'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pin-usb-irq
```

Verify after reboot:

```bash
cat /proc/irq/<N>/smp_affinity_list
# Should show the P-core number you set (e.g., 2)
```

## Multiple IRQ Targets

If multiple USB controllers (e.g., xhci_hcd on different PCI buses) need pinning, add multiple `ExecStart` lines:

```systemd
[Service]
ExecStart=/bin/sh -c 'echo 2 > /proc/irq/138/smp_affinity_list'
ExecStart=/bin/sh -c 'echo 3 > /proc/irq/139/smp_affinity_list'
```

## Alternative: Temporary via shell

```bash
# Immediate, not persistent across reboot
echo 2 | sudo tee /proc/irq/138/smp_affinity_list
```

## When to Use

- USB IRQ landed on an E-core (12-19 on Arrow Lake)
- Input latency is perceptible in terminal/keyboard response
- After sleep/resume, IRQ affinity may reset — the systemd service survives this
