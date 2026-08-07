# Libinput Acceleration Profiles — Flat vs Adaptive

## The Issue
libinput defaults to `adaptive` acceleration — mouse pointer speed changes dynamically based on movement velocity. This is equivalent to Windows' "Enhance pointer precision" (registry key `HKEY_CURRENT_USER\Control Panel\Mouse\MouseSpeed=1`). Many users perceive it as inconsistent, laggy, or "smoothing/filtering" because small movements are slowed and fast movements are accelerated — you never get predictable 1:1 tracking.

## Available Profiles

| Profile | Behavior | Windows equivalent | Latency |
|---------|----------|-------------------|---------|
| `flat` | 1:1 linear, no acceleration. Every pixel of mouse movement = 1 pixel of cursor movement (multiplied by speed setting). | `MouseSpeed=0` (no enhance) | Lowest, predictable |
| `*adaptive` (default) | Dynamic curve: slow movements slowed further (precision), fast movements accelerated. | `MouseSpeed=1` (enhance pointer precision) | Variable, feels laggy at low speed |
| `custom` | User-defined acceleration curve via libinput `AccelConfig`. | Custom driver profiles | Configurable |

## Detection
```bash
sudo libinput list-devices 2>&1 | grep -A 30 'Corsair.*Mouse\|Mouse by' | grep "Accel profiles"
# Output: Accel profiles: flat *adaptive custom
#         Accel profiles: n/a
# The * indicates the active profile.
```

## Fix: Set Flat Profile Permanently (Wayland-Compatible)

### Via libinput quirks file (MOST RELIABLE on Wayland)

Create `/etc/libinput/local-overrides.quirks`:
```
[Device Name]
MatchName=Exact device name from libinput list-devices
AccelProfile=Flat
```

Example:
```
[Corsair Katar Pro XT]
MatchName=Corsair CORSAIR KATAR PRO XT Gaming Mouse
AccelProfile=Flat

[BY Tech Thor 230 Mouse]
MatchName=BY Tech Thor 230 Mouse
AccelProfile=Flat
```

Apply: `sudo mkdir -p /etc/libinput && sudo cp file /etc/libinput/local-overrides.quirks`
Then **replug the device or re-login** — libinput re-reads quirks on device connect.

### Via KDE System Settings (KDE Wayland)
System Settings → Input Devices → Mouse → Pointer Acceleration → "Flat"

### What DOES NOT work on Wayland
- `xinput set-prop` — X11 only, errors or no-op on native Wayland apps
- `nvidia-settings` cursor/pointer settings — NV-CONTROL not available on Wayland

## Verification After Change
```bash
sudo libinput list-devices 2>&1 | grep -A 30 "Corsair.*Mouse" | grep "Accel"
# Before: Accel profiles: flat *adaptive custom
# After:  Accel profiles: *flat adaptive custom
#         Accel profiles: n/a
```

## Combined with USB HID 1ms Polling
For maximum linear response:
1. `usbhid.mousepoll=1` in GRUB (1ms kernel polling)
2. hwdb `MOUSE_POLL=1` (1000Hz device polling)
3. libinput `AccelProfile=Flat` (no acceleration curve)
4. `usbhid.quirks=0x40` (always-poll USB path)
5. `usbcore.autosuspend=-1` (no USB sleep)
