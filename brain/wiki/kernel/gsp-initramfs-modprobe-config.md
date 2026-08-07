---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [gsp-xwayland-crash-chain, pin-irqs-dynamic-v4]
---

# Modprobe Config Must Be Baked Into Initramfs

`/etc/modprobe.d/` config files for NVIDIA kernel parameters are only effective if baked into the initramfs.

## Problem

The NVIDIA kernel module (`nvidia`) loads **from the initramfs** during early boot, before the root filesystem is mounted. Modprobe config files on the root filesystem are ignored because the module has already loaded with default parameters.

## Symptom

After adding `options nvidia NVreg_EnableGpuFirmware=0` to `/etc/modprobe.d/nvidia-perf.conf`:
```bash
nvidia-smi --query-gpu=gsp.mode.current --format=csv
# Still shows: Enabled
```

Even after reboot — because the parameter was never read.

## Fix

Rebuild the initramfs to bake the modprobe config in:

```bash
sudo mkinitcpio -P
sudo reboot
```

`mkinitcpio -P` regenerates all initramfs images. The next boot picks up the config during the initramfs stage before `nvidia` module loads, so the parameter takes effect properly.

## Test

```bash
nvidia-smi --query-gpu=gsp.mode.current --format=csv
# Should show: Disabled
```
