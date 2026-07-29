# USB Input Device Autosuspend — Disable via udev Rules

The kernel parameter `usbcore.autosuspend=-1` disables USB autosuspend globally. For surgical per-device control (e.g., keyboard only, mouse only), use udev rules instead.

## Finding Device IDs

```bash
# List USB devices with vendor:product
lsusb

# Get detailed udev attributes for a specific input device
udevadm info -a -n /dev/input/by-path/pci-*-usb-*-event-kbd
```

## udev Rule Format

```udev
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="VVVV", ATTRS{idProduct}=="PPPP", ATTR{power/autosuspend}="-1"
```

Single rule file per class (e.g., `/etc/udev/rules.d/90-usb-input-noautosuspend.rules`):

```sh
sudo tee /etc/udev/rules.d/90-usb-input-noautosuspend.rules << 'EOF'
# BY Tech Thor 230 keyboard - disable autosuspend
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="331a", ATTRS{idProduct}=="5020", ATTR{power/autosuspend}="-1"

# Corsair KATAR PRO XT mouse - disable autosuspend
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", ATTRS{idProduct}=="1bac", ATTR{power/autosuspend}="-1"
EOF
```

## Apply

```sh
sudo udevadm control --reload-rules
sudo udevadm trigger -v -s usb -a idVendor=331a
```

Verify: `cat /sys/bus/usb/devices/*/power/autosuspend | grep -v '\-1'` should return empty for your input devices.

## Trade-off vs Global

| Approach | Coverage | Maintenance |
|---|---|---|
| `usbcore.autosuspend=-1` (GRUB) | All USB devices | Single param |
| udev rules (per-device) | Selected devices only | Need IDs per device |

Use per-device udev when you want other USB devices (storage, hubs) to still autosuspend for power saving. Use the GRUB param for pure low-latency workstations.
