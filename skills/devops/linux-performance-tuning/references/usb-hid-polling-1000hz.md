# USB HID Polling 1000Hz Configuration

Real-world configuration for Corsair Katar Pro XT Gaming Mouse + BY Tech Thor 230 (wireless headset with keyboard/mouse interface) on Manjaro KDE Wayland + NVIDIA.

## Hardware

| Device | VID:PID | Event Nodes | Notes |
|--------|---------|-------------|-------|
| Corsair Katar Pro XT | `1b1c:1bac` | event-mouse + event-kbd (on same USB dongle, separate HID interfaces) | Gaming mouse, supports 1000Hz via bInterval=1 |
| BY Tech Thor 230 | `331a:5020` | event-mouse + event-kbd (headset combo) | Budget wireless, may not support 1000Hz |

## Three-Layer Fix Applied

### Layer 1 — hwdb (libinput-level override)

File: `/etc/udev/hwdb.d/71-corsair-polling.hwdb`

```
# Corsair Katar Pro XT Gaming Mouse 1000Hz
evdev:input:b0003v1b1Cp1bac* MOUSE_POLL=1

# BY Tech Thor 230 — attempt 1000Hz
evdev:input:b0003v331Ap5020* MOUSE_POLL=1
```

**NOTE**: The BY Tech Thor 230 (USB VID 331a, PID 5020) is a wireless headset. Its keyboard/mouse interfaces go through the same dongle but the device firmware may not support sub-2ms polling. If evtest shows no improvement after applying the hwdb, the hardware is the bottleneck — not configurable in software.

### Layer 2 — Kernel usbhid.mousepoll/kbpoll

Already set via GRUB:
```
usbhid.mousepoll=1 usbhid.kbpoll=1
```

Verified: `cat /sys/module/usbhid/parameters/mousepoll` → `1`, `kbpoll` → `1`

### Layer 3 — usbhid.quirks + autosuspend (GRUB)

```
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40 usbcore.autosuspend=-1
```

`0x40` = `HID_QUIRK_ALWAYS_POLL` — device never enters USB suspend, events flow immediately.

### Identifying Devices

```bash
# Map event nodes to input devices
for ev in /sys/class/input/event*/device/name; do
  echo "$(basename $(dirname $ev)): $(cat $ev)"
done | grep -E "mouse|kbd|Corsair|Thor|keyboard" -i

# Find USB path for event
ls -la /dev/input/by-path/*-event-kbd
# → pci-0000:80:14.0-usb-0:8:1.3-event-kbd (Corsair keyboard on port 8)
# → pci-0000:80:14.0-usb-0:7:1.0-event-kbd (Thor keyboard on port 7)

# Get USB tree
lsusb -t | grep -E "1b1c|331a" -A3
```

## Verification

```bash
# 1. Check kernel params
cat /proc/cmdline | grep -E "usbhid|autosuspend"

# 2. Check usbhid param values
cat /sys/module/usbhid/parameters/mousepoll
cat /sys/module/usbhid/parameters/kbpoll

# 3. Check hwdb loaded
sudo libinput quirks list 2>/dev/null | grep -i corsair

# 4. Raw event timing (move mouse fast for 3s, check deltas)
sudo evtest --grab /dev/input/by-id/usb-Corsair_CORSAIR_KATAR_PRO_XT_Gaming_Mouse_*-event-mouse
# Expected: sub-2ms deltas between POINTER_MOTION events during fast sweep
# If deltas are 4-8ms: hwdb not applied or device doesn't support 1000Hz

## Autosuspend Verification
for dev in /sys/bus/usb/devices/*/product; do
  product=$(cat $dev 2>/dev/null)
  dir=$(dirname $dev)
  if [ -e "$dir/power/autosuspend" ]; then
    echo "$product: autosuspend=$(cat $dir/power/autosuspend)"
  fi
done
# autosuspend=-1 means disabled (optimal for input)
