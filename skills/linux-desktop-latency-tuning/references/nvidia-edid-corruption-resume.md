# NVIDIA EDID Corruption After Resume

## Problem

After S3 sleep/wake on NVIDIA + DisplayPort, the driver fails to re-read the monitor's EDID. The kernel log shows:

```
[drm:nv_drm_semsurf_wait_fence_work_cb [nvidia_drm]] *ERROR*
Failed to register auto-value-update on pre-wait value for sync FD semaphore surface
```

The NVIDIA driver substitutes a fake 128-byte "NVD" placeholder EDID:
- Manufacturer: `NVD` (NVIDIA, not the real monitor brand)
- Only timing: `640x480@59.94 Hz`
- All 4 detailed timing descriptors: Empty

Result: display stuck at 640x480@60Hz after every sleep/wake cycle until reboot.

## Diagnosis

### 1. Check current modes
```bash
cat /sys/class/drm/card0-DP-*/modes
```

### 2. Verify EDID source
```bash
cat /sys/class/drm/card0-DP-3/edid | edid-decode -
# Look for: Manufacturer: NVD → corrupted, should be real manufacturer (HPN, DEL, etc.)
```

### 3. Check kernel errors on resume
```bash
journalctl -b -k | grep "auto-value-update"
```

## Root Cause

The NVIDIA DRM driver's DP AUX/DDC channel fails to re-establish after the DisplayPort link goes down during suspend. The `__nv_drm_semsurf_wait_fence_work_cb` error indicates a sync/semaphore issue in the GPU scheduler, which cascades into a failed EDID read. The DPCD/DDC bus is alive again after resume but the NVIDIA driver's internal state machine doesn't retry the EDID read properly — it falls back to a hardcoded 640x480 EDID.

This is a **driver-level bug specific to NVIDIA's proprietary DRM+KMS stack**. It does NOT affect AMDGPU or Intel DRM because those drivers handle EDID re-read differently after DP link reset.

## Fix: Three-Part Approach

### Part 1 — Capture the Real EDID via DDC

The kernel's DRM EDID is corrupt, but the monitor still responds via DDC/I2C. Use `ddcutil` or direct i2c-dev access:

```bash
python3 -c "
import fcntl, os
I2C_SLAVE = 0x0703
bus = os.open('/dev/i2c-4', os.O_RDWR)
fcntl.ioctl(bus, I2C_SLAVE, 0x50)
os.write(bus, bytes([0x00]))
edid = os.read(bus, 128)
os.close(bus)
with open('/tmp/edid.bin', 'wb') as f:
    f.write(edid)
print(f'EDID saved: {len(edid)} bytes, checksum OK: {sum(edid) % 256 == 0}')
"
```

Verify with `edid-decode /tmp/edid.bin`.

**Finding the right I2C bus:**
```bash
ddcutil detect --verbose | grep 'I2C bus'
# Look for the nvidia i2c adapter associated with your display connector
```

### Part 2 — Install as Firmware + GRUB Param

```bash
sudo mkdir -p /lib/firmware/edid
sudo cp /tmp/edid.bin /lib/firmware/edid/<monitor-model>.bin
```

Add to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`:
```
drm.edid_firmware=DP-3:edid/<monitor-model>.bin
```

The format is: `drm.edid_firmware=<CONNECTOR>:edid/<filename>.bin`
- Replace `<CONNECTOR>` with the DRM connector name (e.g., DP-3, HDMI-A-1)
- The kernel resolves paths relative to `/lib/firmware/`
- Only the base EDID block (128 bytes) is required — extensions are optional but nice to have

Then:
```bash
sudo update-grub
sudo reboot
```

### Part 3 — Resume Hook Output Toggle

Even with the correct EDID firmware, the DP link may need a nudge to apply the modes. Add to the `post)` phase of the systemd-sleep hook:

```bash
# Toggle display off/on to force DP link re-negotiation
kscreen-doctor output.DP-3.disable 2>/dev/null || true
sleep 2
kscreen-doctor output.DP-3.enable 2>/dev/null || true
sleep 1
kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
```

## Limitations

- **Extension blocks are often unreadable via DDC on NVIDIA GPUs**: Attempting to read EDID extension blocks (for 165Hz timings) through the NVIDIA DDC interface may return copies of the base block. The segment register switching (i2c addr 0x30) may not work properly on NVIDIA's i2c adapter. Workaround: the base EDID's range limits (e.g., 60-165Hz) combined with the GPU's driver usually allow adding 165Hz as a custom mode.
- **Reboot required after GRUB change**: `drm.edid_firmware` is a kernel cmdline parameter — it only takes effect on next boot.
- **Only tested on NVIDIA proprietary driver**: Will not work with Nouveau.
