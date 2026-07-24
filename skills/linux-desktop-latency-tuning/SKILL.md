---
name: linux-desktop-latency-tuning
description: Systematic workstation input/response latency tuning for Linux desktops — KDE Wayland, NVIDIA, Intel/AMD CPUs, USB HID optimization, compositor tuning, and sleep/resume resilience. Delivers commands directly, no clarifying questions, lists all options at once.
---

# Linux Desktop Latency Tuning

Systematic methodology for diagnosing and reducing input lag (keyboard, mouse, typing feel) and system response latency on Linux desktop workstations. Covers the full stack: kernel → USB/HID → input stack → compositor/Wayland → display.

## User Interaction Style
When using this skill, the user prefers:
- **Commands listed directly without being asked to choose** — provide all options simultaneously, let them select
- **No clarifying questions** — if multiple approaches exist, list all with their trade-offs and let the user decide
- **Direct answers first** — one-line summary, then details below
- **Sa (yes) / No shorthand** — user confirms with "s", "a", "sa", "fa" for yes/agreement

## When to Use

- User reports "input lag", "typing delay", "mouse deceleration", "sluggish desktop feel"
- After sleep/wake cycles, latency regresses
- Setting up a new workstation for low-latency desktop work (browser, terminal, coding)
- Tuning an NVIDIA+Wayland+KDE system

## Methodology — Layered Investigation

Always investigate top-to-bottom; fix the biggest bottleneck first:

```
1. Kernel cmdline (preempt, threadirqs, c-states)
2. CPU scheduler + governor + power profiles
3. USB HID stack (polling, quirks, hwdb, autosuspend)
4. Input stack (libinput, xinput, keyd, input method)
5. Compositor (KWin effects, VSync, latency policy, animations)
6. Display (refresh rate, VRR, GPU clocks)
7. Sysctl (swappiness, dirty ratio, hugepages)
8. Sleep/resume resilience (systemd-sleep hooks)
```

## Step-by-Step

### 1. Kernel Cmdline Audit
Check current: `cat /proc/cmdline | tr ' ' '\n'`

Essential low-latency params (add to GRUB_CMDLINE_LINUX_DEFAULT):
```
preempt=full           # Full preemption (lowest sched latency)
threadirqs             # Threaded IRQ handlers (respects smp_affinity)
intel_idle.max_cstate=1 # Disable deep C-states (1µs vs 1000µs wake latency)
processor.max_cstate=1 # Belt-and-suspenders for C-state limit
usbhid.mousepoll=1     # 1ms kernel HID mouse polling
usbhid.kbpoll=1        # 1ms kernel HID keyboard polling
usbhid.quirks=0xVID:0xPID:0x40  # Low-latency HID path per device
usbcore.autosuspend=-1 # Global USB never sleeps (or use per-device udev, see references/usb-autosuspend-udev.md)
cpufreq.default_governor=performance

**IOMMU latency note**: `intel_iommu=on` adds DMA translation overhead to GPU buffer exchanges. For gaming/low-latency workstations, consider `iommu=pt` with `igfx_off` to limit overhead. See references/iommu-latency-impact.md (or /brain query "IOMMU latency").
pcie_aspm.policy=performance
workqueue.power_efficient=false
```

### 2. CPU Governor & Power Profiles
- **Check**: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`
- **Fix**: `sudo systemctl disable --now power-profiles-daemon` (overrides governor)
- **KDE PowerDevil**: Check `~/.config/powerdevilrc` for unexpected idle/suspend config

**IRQ pinning**: USB controllers may land on E-cores. Use a systemd oneshot to pin USB IRQs to P-cores — see `references/irq-pinning-systemd.md`.

### 3. USB HID Optimization
**hwdb 1000Hz polling** (no reboot):
```
/etc/udev/hwdb.d/71-corsair-polling.hwdb:
  evdev:input:b*v1B1Cp1BAC*
   MOUSE_POLL=1
```
Apply: `sudo systemd-hwdb update && sudo udevadm trigger`

**usbhid.quirks** (GRUB):
Format: `usbhid.quirks=0xVID:0xPID:0x40,0xVID2:0xPID2:0x40`
Flag 0x40 = HID_QUIRK_ALWAYS_POLL (never skip interrupts, no autosuspend).

**Verify**: `cat /sys/module/usbhid/parameters/quirks`
`udevadm info /dev/input/by-id/usb-*event-mouse 2>&1 | grep MOUSE_POLL`

### Libinput Acceleration Profile

libinput defaults to `adaptive` acceleration — pointer speed changes dynamically with movement velocity (like Windows "Enhance pointer precision"). This causes inconsistent feel and perceived lag.

### Profiles

| Profile | Behavior | Windows equivalent |
|---------|----------|-------------------|
| `flat` | 1:1 linear, predictable | `MouseSpeed=0` (no enhance) |
| `*adaptive` (default) | Speed changes with velocity | `MouseSpeed=1` (enhance) |
| `custom` | Custom curve | Custom driver |

### Detection
```bash
sudo libinput list-devices 2>&1 | grep -A 30 'Corsair.*Mouse' | grep Accel
# * marks active: flat *adaptive custom → adaptive is active
```

### Fix: Flat Profile via libinput Quirks (Works on Wayland)

Create `/etc/libinput/local-overrides.quirks`:
```
[Device Name]
MatchName=Exact device name from libinput list-devices
AccelProfile=Flat
```
Then replug device or relogin. libinput re-reads quirks on device connect.

**Does NOT work on Wayland**: `xinput set-prop`, `nvidia-settings` pointer controls.

See `references/libinput-flat-accel.md` for full details.

### 4. KWin / Compositor Tuning
**Latency policy** (KDE 6):
```
kwriteconfig5 --file kwinrc --group Compositing --key LatencyPolicy LowLatency
```

**Disable compositing** (maximum reduction — no compositor pipeline delay):
```
kwriteconfig5 --file kwinrc --group Compositing --key Enabled false
```

**Alternative — compositing ON but low-latency**:
```
kwriteconfig5 --file kwinrc --group Compositing --key AnimationSpeed 0
kwriteconfig5 --file kwinrc --group Compositing --key GLVSync never
kwriteconfig5 --file kwinrc --group Compositing --key MaxFps 165  # match monitor
kwriteconfig5 --file kwinrc --group Compositing --key AllowTearing true
kwriteconfig5 --file kwinrc --group Compositing --key VrrPolicy FullscreenOnly
```

Apply: `kwriteconfig5 --file kwinrc --group Compositing --key Enabled false`
Restart: `qdbus org.kde.KWin /Compositor resume` (or restart session)

### 5. NVIDIA Wayland Optimizations
**System-wide env vars** (`/etc/environment.d/99-nvidia-wayland.conf`):
```
WLR_NO_HARDWARE_CURSORS=1          # Eliminates cursor stutter on NVIDIA Wayland
GBM_BACKEND=nvidia-drm             # Native GBM on NVIDIA
__GL_SYNC_TO_VBLANK=0              # No forced VSync in apps
__GLX_VENDOR_LIBRARY_NAME=nvidia
QT_QPA_PLATFORM=wayland
XDG_SESSION_TYPE=wayland
```

**PowerMizer**: `nvidia-settings -a '[gpu:0]/GPUPowerMizerMode=1'` (may not work on pure Wayland — no NV-CONTROL X extension). Fallback: `nvidia-smi -pm 1`.

**Verify P-state**: `nvidia-smi -q -d PERFORMANCE | grep 'Performance State'` — P0 is max, P1 is normal desktop idle.

### 6. Sysctl Workstation Tuning
Create `/etc/sysctl.d/99-workstation.conf`:
```
vm.swappiness = 5
vm.dirty_ratio = 5
vm.dirty_background_ratio = 2
vm.page-cluster = 0
kernel.hung_task_timeout_secs = 0
kernel.sched_rt_runtime_us = -1    # CRITICAL — unlimited RT runtime for threaded IRQs. Default 950000 (95%) throttles USB IRQ threads → random lag spikes.
```

**Implicit trap**: `kernel.sched_rt_runtime_us` defaults to 950000 (95%). With `threadirqs`, this throttles USB/keyboard/mouse IRQ threads every second → perceived as random lag spikes. Setting to `-1` (unlimited) is mandatory for low-latency desktop.

Apply: `sudo sysctl --system`

### 7. Hugepages
For workstation use, 512-1024 pages (1-2GB) is sufficient to cover running apps.

**GRUB** — use `hugepages=N` NOT `nr_hugepages=N`:
```
hugepagesz=2M hugepages=512         # GRUB — 'hugepages=' is the correct kernel param
```
The `nr_hugepages=` syntax is passed to userspace and ignored by the kernel on modern builds. Only `hugepages=` triggers boot-time pre-allocation.

**Runtime allocation** (after boot, if GRUB didn't work):
```bash
# Defragment memory first
echo 1 > /proc/sys/vm/compact_memory
sleep 2
# Then allocate — try stepped to handle fragmentation
# Use -ge guard to prevent early break at the first step (256):
TARGET=1024
for pages in 256 512 768 "$TARGET"; do
    echo "$pages" > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null
    CURRENT=$(grep HugePages_Total /proc/meminfo | awk '{print $2}')
    [ "$CURRENT" -ge "$TARGET" ] && break || true
done
```

**Lifecycle**: Fresh boot → full allocation. After S3 sleep, hugepages are freed. Re-allocation often fails because memory is fragmented. The resume hook handles this with `compact_memory` + stepped allocation (see sleep/resume section).

**Verify**: `grep HugePages_Total /proc/meminfo`

**Pitfall**: The stepped allocation loop must use `-ge` to compare against the final target, not `= $pages`. Using `=` causes an early break at the first step (256) because that step succeeds — you never reach the target 1024.

### 8a. Color Range After Sleep (NVIDIA Wayland)
After S3 resume, the DisplayPort link re-negotiates. Sometimes it negotiates limited RGB range (16-235) instead of full (0-255), causing washed-out colors. The NVIDIA driver handles this internally — KDE/KScreen has no control over RGB range on NVIDIA Wayland.

**What you CAN do**:
```bash
# Cycle DPMS to force fresh DisplayPort link negotiation
kscreen-doctor --dpms off 2>/dev/null || true
sleep 2
kscreen-doctor --dpms on 2>/dev/null || true
# Re-apply correct mode
kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
```

**What you CANNOT control** (NVIDIA driver-internal on Wayland):
- RgbRange (full vs limited) — not exposed via KMS
- Color depth / bpc — not exposed via KMS
- Color power preference — driver manages this

**Note**: `nvidia-settings` color queries (DigitalVibrance, ColorSpace, ColorRange) fail on pure Wayland because they require the NV-CONTROL X extension. There is no equivalent for Wayland.

### 8b. EDID Corruption After Resume (NVIDIA Wayland)

After S3 sleep/wake on DisplayPort, the NVIDIA driver may fail to re-read the monitor's EDID, substituting a fake "NVD" placeholder with only `640x480@60Hz`. The kernel log shows:

```
[drm:nv_drm_semsurf_wait_fence_work_cb [nvidia_drm]] *ERROR*
Failed to register auto-value-update on pre-wait value for sync FD semaphore surface
```

This is a known NVIDIA proprietary driver bug — the DP AUX/DDC channel's internal state doesn't recover correctly after DP link drop, and the driver doesn't retry the EDID read.

**Diagnosis:**
```bash
cat /sys/class/drm/card0-DP-*/modes                    # only 640x480 → corrupted
cat /sys/class/drm/card0-DP-3/edid | edid-decode -     # if Manufacturer: NVD → corrupted
journalctl -b -k | grep "auto-value-update"             # DRM semaphore error on resume
```

**Permanent fix (3 parts):**

1. **Capture real EDID via DDC** — the DRM EDID is corrupted but the monitor still responds via I2C:
   ```bash
   # Find i2c bus with: ddcutil detect --verbose | grep 'I2C bus'
   python3 -c "
   import fcntl, os
   bus = os.open('/dev/i2c-N', os.O_RDWR)
   fcntl.ioctl(bus, 0x0703, 0x50)
   os.write(bus, bytes([0x00]))
   edid = os.read(bus, 128)
   os.close(bus)
   open('/tmp/edid.bin','wb').write(edid)
   " && edid-decode /tmp/edid.bin
   ```
   Verify checksum OK and manufacturer matches your monitor (e.g. HPN for HP, DEL for Dell).

2. **Install as firmware + GRUB param:**
   ```bash
   sudo mkdir -p /lib/firmware/edid
   sudo cp /tmp/edid.bin /lib/firmware/edid/<monitor>.bin
   ```
   Add to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`:
   ```
   drm.edid_firmware=DP-3:edid/<monitor>.bin
   ```
   The kernel resolves paths relative to `/lib/firmware/`. Only the 128-byte base block is needed — extension blocks are nice-to-have but often unreadable via NVIDIA DDC.
   
   Then: `sudo update-grub && sudo reboot`

3. **Resume hook output toggle** — even with the correct EDID, the DP link needs a nudge:
   ```bash
   kscreen-doctor output.DP-3.disable 2>/dev/null || true
   sleep 2
   kscreen-doctor output.DP-3.enable 2>/dev/null || true
   sleep 1
   kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
   ```

See `references/nvidia-edid-corruption-resume.md` for full detail.

### 9. Sleep/Resume Resilience
The #1 source of recurring input lag post-tune: fixes don't survive sleep/wake.

**systemd-sleep hook** at `/usr/lib/systemd/system-sleep/latency-fix`:

```bash
#!/bin/bash
# $1 = pre|post, $2 = suspend|hibernate
# CRITICAL: use case "$1" in post) — NOT $2!
HUGE_TARGET=1024    # adjust to match your GRUB hugepages=N
case "$1" in
    post)
        sleep 2
        # 1. Re-apply USB hwdb and quirks
        udevadm trigger --subsystem-match=input
        udevadm trigger --subsystem-match=usb
        udevadm settle --timeout=3
        # 2. Re-allocate hugepages (stepped, with -ge guard)
        for pages in 256 512 768 "$HUGE_TARGET"; do
            echo "$pages" > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null
            CURRENT=$(grep HugePages_Total /proc/meminfo | awk '{print $2}')
            [ "$CURRENT" -ge "$HUGE_TARGET" ] && break || true
        done
        # 3. Re-apply CPU governor + intel_pstate persistence
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo performance > "$cpu" 2>/dev/null || true
        done
        echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct 2>/dev/null || true
        [ "$(cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost)" != "1" ] && \
            echo 1 > /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost 2>/dev/null || true
        # C-state lock: /sys/devices/system/cpu/intel_idle/max_cstate may not exist on kernel 7.0+
        # C-states are locked via GRUB processor.max_cstate=1 — this write is best-effort
        echo 1 > /sys/devices/system/cpu/intel_idle/max_cstate 2>/dev/null || true
        # 4. Re-apply sysctl
        sysctl -w vm.swappiness=5 vm.dirty_ratio=5 vm.page-cluster=0 kernel.sched_rt_runtime_us=-1
        # 5. Restart KWin compositor
        qdbus org.kde.KWin /Compositor suspend; sleep 0.5; qdbus org.kde.KWin /Compositor resume
        # 6. Re-apply KWin compositing OFF
        kwriteconfig5 --file /home/*/.config/kwinrc --group Compositing --key Enabled false
        # 7. Force NVIDIA persistence
        nvidia-smi -pm 1
        logger "[latency-fix] Post-sleep fixes applied. HugePages=$HP"
    ;;\nesac
```

Hook requirements:
- File: `/usr/lib/systemd/system-sleep/latency-fix` (NO `.sh` extension — systemd can be picky)
- Permissions: `sudo chmod 755`
- Test: `journalctl -b | grep latency-fix` after next sleep/wake

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `power-profiles-daemon` running | CPU governor resets to powersave | `systemctl disable --now power-profiles-daemon` |
| `case \$2 in post)` in hook | Hook silently does nothing | Change to `case "\$1" in post)` |
| hwdb modalias wrong casing | `MOUSE_POLL` not applied | Use `b*v1B1Cp1BAC*` (uppercase VID/PID) |
| `nr_hugepages=` in GRUB | Boot param ignored; hugepages 0 | Use `hugepages=N` (without `nr_` prefix) |
| `hugepages` re-allocation loop early break | After sleep, hugepages stuck at 256 | Use `-ge` guard against target, not `= $pages`. The `grep -q "HugePages_Total:.*$pages"` form breaks at step 1 |
| CPU governor resets to `powersave` | Random intervals of lag, 800MHz cores | `sudo systemctl disable --now power-profiles-daemon` |
| `intel_idle/max_cstate` sysfs missing on kernel 7.0+ | Hook line 27: "No such file or directory" | Remove from hook — C-states locked by GRUB `processor.max_cstate=1` already |
| udev rule `ATTR{power/autosuspend}` fails | "Could not chase sysfs attribute" on resume | Remove broken rule — `usbcore.autosuspend=-1` in GRUB covers it globally |
| libinput `adaptive` acceleration active | Inconsistent mouse feel, perceived lag/smoothing | Install `AccelProfile=Flat` via `/etc/libinput/local-overrides.quirks` |
| Chrome `--use-gl=angle` on NVIDIA Wayland | Extra GPU pipeline latency from Vulkan translation | Use `--use-gl=egl` (native EGL) instead |
| `kscreen-doctor` RGB range / color power commands | "Unable to parse arguments" | These are NVIDIA driver-internal — NOT exposed by KScreen. Use DPMS cycle instead |
| Transparent HugePages ALWAYS + madvise conflict | THP behavior unpredictable | Match GRUB to kernel config or remove contradiction |
### GSP Firmware and DPMS Wake (NVIDIA Wayland)

The NVIDIA GPU System Processor (GSP) firmware handles DisplayPort link training, power state transitions, and error recovery on RTX 40/50 series GPUs. On driver 595.x with Blackwell (RTX 5060 Ti), the GSP firmware has known bugs:

**Symptoms:**
- DisplayPort monitor black screen on DPMS wake (display sleeps → press key → keyboard lights up but screen stays black)
- NVIDIA Xid 120 (GSP task exception) on suspend
- Display link training failure — monitor LED shows signal but no image

**Fix:**
```ini
# /etc/modprobe.d/nvidia-perf.conf (requires initramfs rebuild)
options nvidia NVreg_EnableGpuFirmware=0 NVreg_PreserveVideoMemoryAllocations=1
options nvidia_drm modeset=1 fbdev=1
```

`NVreg_EnableGpuFirmware=0` disables GSP firmware offloading — display link training and power management are handled by the CPU driver instead. `NVreg_PreserveVideoMemoryAllocations=1` ensures framebuffer state survives power transitions.

**Important**: modprobe.d changes require initramfs rebuild on Arch/Manjaro:
```bash
sudo mkinitcpio -P && sudo reboot
```

Without initramfs rebuild, the nvidia module loads before modprobe.d is read, and the parameters are ignored. Verify with:
```bash
nvidia-smi --query-gpu=gsp.mode.current --format=csv,noheader
```
Should show `Disabled`.

**Trading**: GSP firmware also handles automatic GPU hang recovery. Disabling it means GPU engine errors like Xid 13/32 (dota2 channel timeout) may escalate to harder lockups. Use `RMUseSwLinkTraining=1` in RegistryDwords as a lighter alternative that only fixes DP link training without disabling GSP entirely.

## Verification Commands

Run these to confirm all layers are optimized:
```bash
# Kernel
cat /proc/cmdline | grep -E 'preempt|threadirqs|quirks|cstate|hugepages'

# CPU
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu0/cpuidle/state*/latency

# USB
cat /sys/module/usbhid/parameters/quirks
udevadm info /dev/input/by-id/usb-*mouse 2>&1 | grep MOUSE_POLL

# Compositor
kreadconfig5 --file kwinrc --group Compositing --key Enabled

# Memory
grep HugePages_Total /proc/meminfo

# GPU
nvidia-smi -q -d PERFORMANCE | grep 'Performance State'
echo $WLR_NO_HARDWARE_CURSORS

# Sysctl
sysctl kernel.sched_rt_runtime_us

# Resume hook
ls -la /usr/lib/systemd/system-sleep/latency-fix
journalctl -b | grep latency-fix | tail -3
```

## Chrome on NVIDIA Wayland

Chrome/Chromium's rendering backend choice significantly affects WebGL/Canvas performance on NVIDIA Wayland. The most common pitfall is using `--use-gl=angle` without specifying a backend — ANGLE may fall back to SwiftShader (software) for WebGL rendering.

| `--use-gl=` + `--use-angle=` | Backend | NVIDIA Wayland behavior |
|-------|---------|------------------------|
| `angle` (default, no `--use-angle=`) | ANGLE auto-picks | **May fall back to SwiftShader** (software) → WebGL broken/slow |
| `angle --use-angle=vulkan` | ANGLE → Vulkan | **Recommended** — hardware accelerated, stable on 595.x |
| `desktop` | Native GLX/EGL | Direct path, no SwiftShader risk |

**Recommended flags** (tested on RTX 5060 Ti / 595.71.05 / Manjaro / KDE 6):
```bash
google-chrome-stable --ozone-platform=wayland \
  --use-gl=angle --use-angle=vulkan \
  --ignore-gpu-blocklist \
  --disable-gpu-driver-bug-workarounds \
  --enable-gpu-rasterization \
  --enable-features=VaapiVideoDecoder,VaapiIgnoreDriverChecks
```

**Flags to avoid on NVIDIA Wayland:**
- `--use-gl=angle` alone (bare ANGLE → may pick SwiftShader → GeoGuessr/Maps WebGL broken)
- `--enable-native-gpu-memory-buffers` (rendering corruption on NVIDIA Wayland)

**Safe flags:**
- `--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks` (hardware video decode)
- `--enable-gpu-rasterization` (GPU raster for pages)
- `--ignore-gpu-blocklist`
- `--disable-gpu-driver-bug-workarounds`

**Common Chrome problems and fixes:**

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| GeoGuessr / WebGL games slow or black | ANGLE fell back to SwiftShader | Add `--use-angle=vulkan` to flags |
| Google Maps 3D rendering broken | Same as above | Add `--use-angle=vulkan` |
| GPU context init fails | Bare `--use-gl=angle` | Add `--use-angle=vulkan` or use `--use-gl=desktop` |
| Video decode crashes (Xid 31) | VA-API + IOMMU conflict | Remove `intel_iommu=on` from kernel cmdline |

## References

See `references/` for:
- `gigabyte-z890-xhci.md` — The Gigabyte Z890 xHCI resume error + workaround
- `corsair-katar-pro-xt.md` — Specific USB IDs and quirks for Corsair Katar Pro XT
- `nvidia-wayland-env.md` — NVIDIA Wayland env vars and caveats
- `display-color-post-sleep.md` — Display color after S3 sleep on NVIDIA Wayland
- `libinput-flat-accel.md` — Libinput flat vs adaptive acceleration profiles
- `usb-autosuspend-udev.md` — Per-device USB autosuspend via udev rules (alternative to GRUB global param)
- `irq-pinning-systemd.md` — Pinning USB IRQs to P-cores via systemd oneshot service
- `iommu-latency-impact.md` — IOMMU DMA translation overhead trade-off (in brain wiki at kernel/iommu-latency-impact.md)