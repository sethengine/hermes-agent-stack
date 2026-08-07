---
source_session: "20260711_133754_b5c8e4"
date: 2026-07-11
category: gpu
related: [nvidia-edid-fake-nvd-after-sleep, resume-hook-dp-toggle, hp-x34-display]
---

# EDID Firmware Fix for NVIDIA Post-Sleep Resolution

Permanent fix for the NVIDIA DRM post-sleep fake NVD EDID using kernel EDID firmware injection.

## Steps

1. **Capture the real EDID** via DDC/I2C using `ddcutil` while the display is responsive (before sleep):
   ```bash
   mkdir -p /lib/firmware/edid
   ddcutil getvcp 0x60 > /dev/null  # wake DDC
   dd if=/dev/i2c-$(i2cdetect -l | grep "NVIDIA.*DP-3" | cut -d- -f2 | awk '{print $NF}') \
      of=/lib/firmware/edid/hp-x34.bin bs=128 count=1 skip=80 2>/dev/null
   ```

2. **Add kernel parameter** to force EDID injection:
   ```
   drm.edid_firmware=DP-3:edid/hp-x34.bin
   ```
   Add to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then `sudo grub-mkconfig -o /boot/grub/grub.cfg`.

3. **Reboot** — the kernel now uses the captured real EDID on every resume instead of NVIDIA's fake NVD fallback.

## Notes

- Extension blocks (for 165Hz) may not be readable via DDC on NVIDIA GPUs — the 128-byte base block provides the critical 3440×1440 base timing and 60-165Hz range.
- Works alongside the [[resume-hook-dp-toggle]] to ensure modes are properly applied after the EDID is in place.
- Requires one-time I2C capture — the firmware blob is permanent once saved.
