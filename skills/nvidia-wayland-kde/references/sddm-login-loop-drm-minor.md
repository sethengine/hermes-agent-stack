# SDDM Login Loop — simpledrm Grabs DRM Minor 0 Before nvidia-drm

## Symptom

- Kernel boots fine to SDDM login screen
- Entering credentials → screen flashes → returns to SDDM login
- Infinite loop — the KDE Wayland session (kwin_wayland) crashes immediately on start
- Works under a different kernel (same initramfs, same modprobe config, same cmdline)

## Root Cause

simpledrm (built-in) creates `/dev/dri/card0` on DRM minor 0 **before** nvidia-drm loads.  
nvidia-drm gets pushed to minor 1 → `/dev/dri/card1`.

kwin_wayland opens `/dev/dri/card0` expecting the NVIDIA GPU, finds the simpledrm framebuffer dummy instead, and crashes. SDDM recycles (login → crash → login loop).

### The Exact dmesg Difference

**Working kernel (simpledrm suppressed):**
```
The simpledrm driver will not be probed
...
[drm] Initialized nvidia-drm 0.0.0 for 0000:02:00.0 on minor 0
```

**Broken kernel (simpledrm steals minor 0):**
```
simple-framebuffer simple-framebuffer.0: [drm] Registered 1 planes with drm panic
[drm] Initialized simpledrm 1.0.0 for simple-framebuffer.0 on minor 0
simple-framebuffer simple-framebuffer.0: [drm] fb0: simpledrmdrmfb frame buffer device
...
[drm] Initialized nvidia-drm 0.0.0 for 0000:02:00.0 on minor 1
```

## Why simpledrm Suppression Fails on Some Kernels

The kernel cmdline `nvidia_drm.modeset=1` normally triggers a code path in `sysfb_simplefb.c` that skips simpledrm probing (deferring to nvidia-drm). This suppression works on the stock kernel but **not on the custom kernel**, likely due to:

- **Compiler optimization**: O3 (vs O2) changes initcall ordering — simpledrm's initcall may run before the `nvidia_drm.modeset=1` check
- **Scheduler patches** (BORE, CACHY): Can reorder driver init sequences
- **Different microarchitecture target** (x86-64 v3): Different binary layout affects linker-level initcall ordering

The kernel configs themselves are **nearly identical** for DRM options — the difference is in the compiler/toolchain, not the config.

## Diagnostic Commands

### 1. Identify the boot with the crash
```bash
journalctl --list-boots
```
Look for boots with short durations.

### 2. Check DRM initialization in previous boot
```bash
journalctl -k -b -3 --no-pager | grep -E 'simpledrm|nvidia-drm.*minor'
```

### 3. Compare across kernels
```bash
# Boot -2, -3, -4 etc.
for b in -2 -3 -4; do echo "=== Boot $b ==="; journalctl -k -b $b --no-pager | grep -E 'simpledrm|nvidia-drm.*minor'; done
```

### 4. Check current DRM device → GPU mapping
```bash
for c in /sys/class/drm/card*; do
  echo "$c -> device=$(cat $c/device/device 2>/dev/null) vendor=$(cat $c/device/vendor 2>/dev/null)"
done
```
`0x10de` = NVIDIA, `0x8086` = Intel.

### 5. Check framebuffer devices
```bash
cat /proc/fb
```
`0 EFI VGA` = EFI framebuffer (harmless). `simpledrmdrmfb` = simpledrm created a DRM device.

### 6. Compare kernel configs between working and broken kernels
```bash
# Current (working) kernel config
zcat /proc/config.gz > /tmp/config-working

# Target kernel config (from build directory)
grep '=y' /usr/lib/modules/7.1.4-1-cachyos-bore/build/.config > /tmp/config-cachyos

# Diff DRM-related options
diff <(grep -E 'DRM|FB|SYSFB' /tmp/config-working | sort) \
     <(grep -E 'DRM|FB|SYSFB' /tmp/config-cachyos | sort)
```

### 7. Verify initramfs contents for NVIDIA modules
```bash
sudo lsinitcpio -l /boot/initramfs-linux-cachyos-bore.img | grep -E 'nvidia.*\.ko'
```

### 8. Check module dependencies
```bash
modinfo -F depends /usr/lib/modules/7.1.4-1-cachyos-bore/extramodules/nvidia-drm.ko.zst
modinfo -F vermagic /usr/lib/modules/7.1.4-1-cachyos-bore/extramodules/nvidia-drm.ko.zst
```

## Fix Options

| # | Fix | Mechanism |
|---|-----|-----------|
| 1 | `sysfb.disable=1` in kernel cmdline | Prevents the system firmware framebuffer from registering as a platform device — simpledrm has nothing to bind to |
| 2 | `simpledrm.remove=1` in kernel cmdline | Unregisters simpledrm driver entirely |
| 3 | Remove `nvidia_drm.fbdev=0` from modprobe.d | nvidia-drm provides fbdev, changing init order |
| 4 | Add nvidia modules earlier in initramfs MODULES | Ensures nvidia-drm loads before simpledrm probes |

## Verification After Fix

```bash
# Should see nvidia-drm on minor 0
journalctl -b -k --no-pager | grep 'nvidia-drm.*minor'

# Should NOT see simpledrm initialization
journalctl -b -k --no-pager | grep -i simpledrm
```

## Related

- The `nvidia_drm.modeset=1` kernel parameter is the intended suppression mechanism for simpledrm — when it fails, the symptom is this login loop
- Always compare actual boot logs (`journalctl -k -b -N`) rather than assuming both kernels behave the same — in this investigation, the user assumed simpledrm was suppressed on both kernels, but journalctl proved otherwise
