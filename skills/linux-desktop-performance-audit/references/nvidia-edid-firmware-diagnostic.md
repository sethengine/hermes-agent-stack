# NVIDIA Custom EDID Firmware — Diagnostic Pattern

## Signal

```
$ sudo dmesg | grep -i "edid\|firmware"
[   10.483102] nvidia 0000:02:00.0: [drm] *ERROR* Invalid firmware EDID "edid/hp-x34.bin"
```

This error fires when the NVIDIA DRM driver can't parse a custom EDID firmware file specified via `drm.edid_firmware=CONNECTOR:edid/filename.bin`.

## Diagnostic Steps

```bash
# 1. Check if the override is in cmdline
cat /proc/cmdline | grep "drm.edid_firmware"

# 2. Check the file size — valid EDID is 128 bytes (EDID 1.0) or 256 bytes (EDID 1.3+)
ls -la /usr/lib/firmware/edid/<filename>.bin
# If only 128 bytes AND the kernel rejects it → file is incomplete/corrupt

# 3. Inspect the file contents
xxd /usr/lib/firmware/edid/<filename>.bin | head -5
# EDID header must start with: 00 FF FF FF FF FF FF 00

# 4. Extract the monitor's actual EDID for comparison
sudo cat /sys/class/drm/card0-<CONNECTOR>/edid > /tmp/real-edid.bin
ls -la /tmp/real-edid.bin
edid-decode /tmp/real-edid.bin

# 5. If the custom EDID was meant to override resolution/refresh:
#    - Verify the override is actually needed (does the monitor natively support the desired mode?)
#    - If not needed, remove drm.edid_firmware= from GRUB_CMDLINE_LINUX_DEFAULT
```

## Root Causes

1. **Truncated EDID binary**: File is too short — only 128 bytes of header, no actual EDID data
2. **Wrong path/syntax**: `drm.edid_firmware=DP-3:edid/filename.bin` requires "/usr/lib/firmware/edid/filename.bin" to exist
3. **NVIDIA parser stricter than kernel**: Even if the kernel's firmware loader accepts a short file, the NVIDIA DRM driver may reject it

## Fix Options

### Option A: Replace with valid EDID
```bash
sudo cat /sys/class/drm/card0-DP-3/edid > /tmp/real-edid.bin
sudo cp /tmp/real-edid.bin /usr/lib/firmware/edid/hp-x34.bin
# Reboot
```

### Option B: Remove the override entirely
```bash
# Edit /etc/default/grub, remove "drm.edid_firmware=DP-3:edid/hp-x34.bin"
# from GRUB_CMDLINE_LINUX_DEFAULT, then:
sudo grub-mkconfig -o /boot/grub/grub.cfg
# Reboot
```

## Verify Fix
```bash
sudo dmesg | grep -i "edid\|firmware" | grep -v "DMAR\|INTR-REMAP"
# Should show no "Invalid firmware EDID" errors
```
