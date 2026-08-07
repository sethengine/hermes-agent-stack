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
- **Investigation ends in commands, not questions** — after an audit, put the fix commands directly in the response (ranked, copy-pasteable); do NOT use the clarify tool to ask which fixes to apply (user: "just give the commands")

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

### Fix: Flat Profile via KWin D-Bus (Wayland-native, per-device)

On KDE Wayland, KWin exposes per-device input properties over D-Bus — no root, no quirks, applies immediately. This is the correct Wayland method:

```bash
# Resolve the KWin InputDevice object path for the mouse (event basename)
EVENT=$(basename $(readlink /dev/input/by-id/*Corsair*KATAR*event-mouse* | head -1))
qdbus6 org.kde.KWin /org/kde/KWin/InputDevice/$EVENT \
  org.freedesktop.DBus.Properties.Set \
  org.kde.KWin.InputDevice pointerAccelerationProfileFlat true
qdbus6 org.kde.KWin /org/kde/KWin/InputDevice/$EVENT \
  org.freedesktop.DBus.Properties.Set \
  org.kde.KWin.InputDevice pointerAccelerationProfileAdaptive false
qdbus6 org.kde.KWin /org/kde/KWin/InputDevice/$EVENT \
  org.freedesktop.DBus.Properties.Set \
  org.kde.KWin.InputDevice pointerAcceleration 0.0
```

- **Runtime-only** — not persisted to kwinrc; re-apply at login via `~/.config/autostart/mouse-flat.desktop` (X-KDE-autostart-phase=2) with a 3s `sleep` first so KWin is up.
- Object path = the input event basename (e.g. `event8`), matched via `/dev/input/by-id/*<vendor>*event-mouse`.
- Only covers devices named in the script — add a block per mouse (e.g. BY Tech Thor 230) if used.
- Combines fine with libinput quirks if root-level enforcement is preferred; D-Bus is the Wayland-native path.

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

**VRR on the desktop = input lag culprit on NVIDIA Wayland** (confirmed 2026-08, RTX 5060 Ti / HP X34):
- `VrrPolicy=2` (shows as `Vrr: Automatic` in `kscreen-doctor -o`) leaves AdaptiveSync active for ANY window, including the desktop. The monitor refresh hunts down to its VRR floor (~48 Hz on the HP X34) → the whole desktop feels laggy even with CPU/GPU idle.
- **Diagnostic**: `journalctl -b | grep 'Frame latency is negative'` — Chrome's viz compositor logs this (display.cc:272) when presentation timing goes negative under desktop VRR. Also check `kscreen-doctor -o | grep Vrr` → `Automatic` is the bad state.
- **Fix**: `kwriteconfig6 --file kwinrc --group Compositing --key VrrPolicy 0` (Never) or `3` (FullscreenOnly — VRR only in fullscreen games). Apply live: `qdbus6 org.kde.KWin /Compositor reinitialize`. User reported the desktop became "amazing" after this — the single biggest perceived-lag fix of the audit.
- Enum: `0`=Never, `1`=Always, `2`=Automatic (per-window, desktop included), `3`=FullscreenOnly.
- See `references/vrr-desktop-lag-nvidia-wayland.md`.

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

### 5b. Env-Var Source Priority & Conflict Hunting (global audit)

When auditing "all env vars" for latency/perf, values come from many sources with strict priority for systemd-launched apps. Check every source, then diff for conflicts:

1. `/etc/environment`
2. `/etc/environment.d/*.conf`
3. `~/.config/environment.d/*.conf`  ← overrides sources 1-2 and 4-6 for GUI/systemd apps
4. `~/.config/plasma-workspace/env/*.sh` (KDE session scripts)
5. `/etc/profile.d/*.sh` (shell login — e.g. Manjaro's `qt5-accessibility.sh`)
6. `~/.profile`, `~/.bashrc`, `~/.zshrc` (only for shell-launched processes)

Typical conflicts found in audits:
- Same var, different values in `.profile` vs `environment.d` (e.g. `__GL_SHADER_DISK_CACHE_SIZE` 1G vs 10G — environment.d wins for GUI apps; `.profile` only affects shell-launched).
- Mutually exclusive flags both set (`PROTON_ENABLE_FSYNC=1` + `PROTON_ENABLE_ESYNC=1` — fsync silently wins; delete the loser).
- Inert vars on non-wlroots compositors (`WLR_NO_HARDWARE_CURSORS` is a wlroots var — meaningless on KWin; KWin uses `KWIN_*`).

### 5c. Process Priority Tier Guard (nice / chrt) & ananicy-cpp
"Some apps and services have so high nice in htop" usually means an auto-nicer
daemon rules the system. On sethengine's box it was **ananicy-cpp** ("ANAother
Auto NIce daemon") — it bumped apps (even Hermes) to nice -8, above plasmashell
(-6), and could push games/electron launchers near KWin, starving the desktop.
Disable it and replace with an explicit guard:
```bash
sudo systemctl disable --now ananicy-cpp.service
```

**The real hierarchy** (schedule class beats nice; RT ignores nice):
```
SCHED_FIFO  prio 90  USB(xhci)+GPU(nvidia) IRQ threads   ← absolute top
SCHED_RR    prio 41  kwin_wayland, keyd                   ← RT, above normal
TS ni -12            pipewire, wireplumber                ← high but PREEMPTIBLE
TS ni  -6            plasmashell                          ← above normal apps
cap ni -10           stray apps (any user)                ← nothing climbs higher
```
`/usr/local/bin/prio-guard` (v2) enforces this at boot + resume (one-shot, not a
daemon). **pipewire must stay TS + high nice, NOT real-time** — a FIFO/RR
pipewire monopolizes a core and blocks everything (the "pipewire bug"). Safety
cap demotes any process (scan ALL users) with nice < -10. See
`references/priority-tier-guard-ananicy-cpupower.md`.

**cpupower.service boot governor** — make the otherwise-no-op service useful:
set `GOVERNOR='performance'` in `/etc/default/cpupower-service.conf` (keys:
GOVERNOR, PERF_BIAS, EPP). Leave EPP unset on HWP (returns -EBUSY; prefer the
MSR read). Prefer this over tmpfiles.d for boot-time governor.

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

**zram — two cases (check `swapon --show` AND RAM size first)**:
- **High-RAM desktop (64GB+)**: zram is pointless and its default swappiness=150 actively hurts — it swaps hot game pages into compressed RAM while real RAM sits free → stutter/input lag. Kill it: shadow the udev rule that writes it (`grep SYSCTL{vm.swappiness} /usr/lib/udev/rules.d/` — CachyOS/Manjaro: `30-zram.rules`), then `udevadm control --reload`, `swapoff /dev/zram0`, mask the zram units, set `vm.swappiness=10`. NOTE: udev rule edits need reload + a NEW event; `udevadm trigger` re-fires the 150 writer.
- **Low-RAM (≤16GB)**: zram is intentional — leave swappiness 150-180 alone. Only disk-only swap wants `vm.swappiness=5`.

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
# NOTE (sethengine): hugepages intentionally DISABLED (VM-only workload) — the
# hugepages block below was removed from this system's hook; omit it here too.

# CRITICAL: systemd-sleep runs hooks as ROOT — root has no access to the
# user's Wayland session (no WAYLAND_DISPLAY, XDG_RUNTIME_DIR, or session bus).
# kscreen-doctor / qdbus WILL fail with "could not connect to display" or
# "no Qt platform plugin could be initialized" unless bridged via runuser.
USER_UID=$(id -u sethengine 2>/dev/null || echo 1000)
USER_RUN=/run/user/$USER_UID
WAY_DISP=$(ls "$USER_RUN"/wayland-* 2>/dev/null | head -1 | xargs -r basename || echo wayland-0)
run_as_user() {
    runuser -u sethengine -- env \
        XDG_RUNTIME_DIR="$USER_RUN" \
        WAYLAND_DISPLAY="$WAY_DISP" \
        QT_QPA_PLATFORM=wayland \
        "$@" 2>/dev/null
}

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
        # 3b. CRITICAL — do NOT rely on the governor re-apply above for cpu0.
        #     After S3 on Gigabyte Z890, firmware can lock cpu0's HWP request MSR
        #     (0x774) at its floor (reads 0x0d0d) → P-core stuck ~400-800MHz while
        #     other cores boost. Governor is a HINT only under HWP; write the MSR.
        #     See references/arrow-lake-hwp-bootcore-lock-resume.md.
        modprobe msr 2>/dev/null || true
        wrmsr -p0 0x774 0x5757 2>/dev/null || true
        # C-state lock: /sys/devices/system/cpu/intel_idle/max_cstate may not exist on kernel 7.0+
        # C-states are locked via GRUB processor.max_cstate=1 — this write is best-effort
        echo 1 > /sys/devices/system/cpu/intel_idle/max_cstate 2>/dev/null || true
        # 4. Re-apply sysctl
        sysctl -w vm.swappiness=5 vm.dirty_ratio=5 vm.page-cluster=0 kernel.sched_rt_runtime_us=-1
        # 5. Force NVIDIA persistence
        nvidia-smi -pm 1
        # 6. Display re-sync — MUST run in the user session via run_as_user
        run_as_user kscreen-doctor output.DP-3.disable
        sleep 2
        run_as_user kscreen-doctor output.DP-3.enable
        sleep 2
        run_as_user kscreen-doctor output.DP-3.mode.3440x1440@165
        # 7. KWin compositor — use qdbus6 (qdbus only exists in /usr/lib/qt6/bin, not on PATH)
        run_as_user qdbus6 org.kde.KWin /Compositor suspend || true
        sleep 0.5
        run_as_user qdbus6 org.kde.KWin /Compositor resume || true
        logger "[latency-fix] Post-sleep fixes applied. HugePages=$HP"
    ;;\nesac
```

Hook requirements:
- File: `/usr/lib/systemd/system-sleep/latency-fix` (NO `.sh` extension — systemd can be picky)
- Permissions: `sudo chmod 755`
- Test: `journalctl -b | grep latency-fix` after next sleep/wake
- To verify the session bridge works BEFORE a resume: `runuser` needs root, but as your user you can test the same env proxy directly:
  ```bash
  env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland \
      kscreen-doctor --outputs
  env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland \
      qdbus6 org.kde.KWin /Compositor active   # prints "true"
  ```

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
| `kscreen-doctor`/`qdbus` in sleep hook fail silently | Screen stays black after wake, or hook's display commands do nothing | Hook runs as **root** — root has no Wayland session. Bridge via `runuser -u <user> -- env XDG_RUNTIME_DIR=/run/user/<uid> WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland <cmd>` (see section 9 hook) |
| `qdbus: command not found` in hook/scripts | D-Bus calls fail | `qdbus` only exists at `/usr/lib/qt6/bin/qdbus` (not on PATH for root/systemd). Use `/usr/bin/qdbus6` instead |
| Multiple systemd services write the same knob (e.g. `intel-min-perf.service` sets `min_perf_pct=25`, `cpu-perf-boot.service` sets 70) | Runtime value matches neither config's intent; first-input lag from idle cores ramping up | Find boot order with `journalctl -b | grep <service>` — the service started LAST wins. Disable the stale/conflicting one. Batch-compare runtime `/proc/sys` vs sysctl.d intent to spot unknown writers (see `references/sysctl-service-conflicts.md`) |
| `energy_performance_preference` (EPP) write under HWP returns `-EBUSY` (Device or resource busy) | A service/script that writes EPP had a red "failed" that worried you — but EPP was ALREADY performance at the hardware level | In HWP mode intel_pstate owns EPP; the sysfs write is refused (`-EBUSY`), NOT "silently clamped". Read the HWP MSR byte instead: `wrmsr -p0 0x774` → bits 31:24 = EPP (`0x00`=perf, `0x40`=bal_perf, `0x80`=bal_pow, `0xff`=power). On sethengine's box it's `0x00` already — don't write EPP, don't flag it. See `references/priority-tier-guard-ananicy-cpupower.md` |
| `rtirq.service` enabled but `threadirqs` missing from kernel cmdline | Journal: "A realtime kernel or the threadirqs kernel parameter are required" + `/etc/rtirq.conf: line 1: -a: command not found` | **threadirqs was REMOVED on sethengine's system (caused problems) — do not re-add.** rtirq can never work without it → disable rtirq. Without threadirqs, IRQs stay hardirq-context on pinned cores. For PipeWire priority use TS + high nice (-12), NOT FIFO/RR — a real-time pipewire monopolizes a core and blocks everything (the "pipewire bug"; see sec 5c & `references/priority-tier-guard-ananicy-cpupower.md`) |
| keyd running while masked | keyd grabs ALL keyboards (`[ids] *`), adds a userspace hop per keypress (SCHED_FIFO 49) | Check intent FIRST: on sethengine's system keyd is INTENTIONAL (key remapping) — do NOT disable; the latency cost is accepted. Only disable if the user confirms it should be masked |
| NetworkManager `wifi.powersave = 3` | `iw dev ... get power_save` shows off at boot but flips ON after reconnect — WiFi latency spikes | NM re-applies power save on every connection, defeating `iw set power_save off` services. Set `wifi.powersave = 2` in `/etc/NetworkManager/conf.d/wifi-powersave.conf`, then `systemctl restart NetworkManager` |
| `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1` (Manjaro `/etc/profile.d/qt5-accessibility.sh`) | at-spi-dbus-bus runs; every Qt app pays a11y overhead (small UI/startup latency) | Override via `~/.config/environment.d/00-a11y-off.conf`: `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=0` (takes effect next login; skip if a screen reader is used) |
| `VrrPolicy=2` (Automatic) in kwinrc | Whole desktop laggy despite idle CPU/GPU; journal: Chrome `Frame latency is negative` (display.cc:272); `kscreen-doctor -o` shows `Vrr: Automatic` | Set `VrrPolicy 0` (Never) or `3` (FullscreenOnly); apply via `qdbus6 org.kde.KWin /Compositor reinitialize` |
| cpu0 stuck at 400–800 MHz after S3 resume while other cores boost; whole desktop abysmal despite free CPU/RAM/thermals | Re-applying the `performance` governor does NOT fix it (governor is only a HWP hint; firmware locked the register's MAX field) | Write the MSR in the resume hook: `modprobe msr; wrmsr -p0 0x774 0x5757`. Verify: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq` under load. This bugs a Gigabyte Z890 firmware HWP re-init defect — see `references/arrow-lake-hwp-bootcore-lock-resume.md` (a one-shot boot service is NOT enough; it must live in the `post`-case systemd-sleep hook) |
| `--use-angle=desktop` in chrome-flags.conf | Invalid ANGLE backend — pair `--use-gl=angle --use-angle=desktop` is ignored, negative frame latency persists | Use `--use-gl=desktop` ALONE (native path) or `--use-gl=angle --use-angle=vulkan` |
| Chrome flag file edited but Chrome not restarted | Old flags still active; timing errors continue after "fix" | Flag changes only apply to a FRESH Chrome start; verify with `tr '\0' ' ' < /proc/<chrome-gpu-pid>/cmdline` |
| udev rule edited (e.g. 30-zram.rules swappiness) but value unchanged | Runtime still shows old value | udev rules need `udevadm control --reload` AND a new matching event; `udevadm trigger` re-fires the OLD rule's write if not reloaded first |
| `sudo sed -i '/min_perf_pct/a\…'` inserted a block multiple times | Same block appears after EVERY line matching the `/anchor/` pattern — a comment and a later line both contained `min_perf_pct`, so the fix was triplicated (it still works — all copies were inside `post)` — but it's sloppy and risks landing in the wrong `case` branch) | Anchor `sed` append on the FULL, unique line, not a bare token. Check for dupes with `grep -c '<needle>'`. To repair: filter the file (`grep -v`) and `sudo install -m 755` it back. Prefer the `patch` tool for a single unique-match replacement |
| Tool refuses to write a sensitive system path (`/lib/systemd/…`, `/usr/lib/…`, `/etc/…`) | Edit tool returns "Refusing to write to sensitive system path" | Those files must be modified via the terminal tool with `sudo` (`sudo sed -i …`, `sudo install -m 755 …`); the `patch`/`write_file` tools are blocked on them by design |
| Bare `wrmsr`/`rdmsr` in a systemd-sleep hook silently no-ops | Hook runs but cpu0 still locked after resume; `journalctl -b | grep latency-fix` shows nothing from the log line | systemd-sleep hooks run with a MINIMAL PATH — `/usr/sbin/wrmsr` isn't found. Always use the full path AND load the module first: `modprobe msr 2>/dev/null || true; /usr/bin/wrmsr -p0 0x774 0x574757`. Then confirm the hook actually executed via its `logger` line in the journal |
| tmpfiles.d used for cpufreq/EPP writes (e.g. `/etc/tmpfiles.d/10-gaming-cpu.conf`) | Config silently never applies; `journalctl`/manual `echo` shows EPP `-EBUSY`, governor not set | tmpfiles.d runs too early — cpufreq/EPP nodes don't exist yet, and EPP returns `-EBUSY` on HWP → dead config. Use cpupower.service for the boot governor + the resume hook for per-wake fixes instead |
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

# Conflicting post-boot writers (see references/sysctl-service-conflicts.md)
cat /proc/sys/vm/swappiness /proc/sys/vm/vfs_cache_pressure /proc/sys/vm/min_free_kbytes /proc/sys/vm/max_map_count
journalctl -b | grep -E 'intel-min|cpu-perf|thp-tune|rtirq|pin-irqs'   # boot order — last start wins
sysctl --system 2>&1 | grep 'Permission denied'                       # reveals hidden 600-perm sysctl.d files
swapon --show                                                          # zram prio>disk ⇒ high swappiness is intentional
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
- `--use-angle=desktop` (NOT a valid `--use-angle=` value — the pair `--use-gl=angle --use-angle=desktop` is ignored entirely; use `--use-gl=desktop` ALONE for the native path, or `--use-gl=angle --use-angle=vulkan`)
- `--enable-native-gpu-memory-buffers` (rendering corruption on NVIDIA Wayland)

**Display timing diagnostic**: `journalctl -b | grep 'Frame latency is negative'` (components/viz/service/display/display.cc:272) = Chrome's presentation timing under desktop VRR. Turn VRR off for the desktop (`VrrPolicy 0`); a Chrome restart is required after any flag change.

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
- `sleep-hook-wayland-session-bridge.md` — systemd-sleep hooks run as root; runuser bridge into the user's Wayland session, qdbus6 vs qdbus, error signatures, non-root test commands
- `sysctl-service-conflicts.md` — detecting systemd services that fight over the same tuning knob (min_perf_pct, EPP, sysctl): runtime-vs-config comparison, boot-order forensics, zram udev-rule writer (two cases: 64GB+ → kill zram; ≤16GB → leave), hidden 600-perm config files
- `vrr-desktop-lag-nvidia-wayland.md` — desktop VRR/AdaptiveSync = perceived lag on NVIDIA Wayland; Chrome `Frame latency is negative` diagnostic; VrrPolicy enum 0-3 + fix
- `arrow-lake-hwp-bootcore-lock-resume.md` — Arrow Lake/Gigabyte Z890 post-resume cpu0 HWP lock (~400MHz); 0x774 reads 0x0d0d; governor can't fix; `wrmsr -p0 0x774 0x5757` in the sleep hook; verified-innocent list (thermal, governor, power daemons, irqbalance)
- `priority-tier-guard-ananicy-cpupower.md` — ananicy-cpp misranking + disable; the prio-guard FIFO>RR>TS hierarchy; pipewire RT-monopoly bug; cpupower.service config mechanism; EPP -EBUSY on HWP (MSR byte decode); tmpfiles.d-wrong-for-cpu pitfall