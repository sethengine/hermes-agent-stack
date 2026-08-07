---
name: linux-latency-tuning
description: Full-stack Linux desktop latency tuning — GRUB kernel params, USB hwdb, KWin compositor, NVIDIA Wayland env, C-states, hugepages, sysctl, resume hooks, mouse acceleration disable. For Intel/NVIDIA KDE Wayland systems.
---

# Linux Latency Tuning

## Background Game Mouse Lag — Priority + Compositor, NOT Memory/TLB

**Refines the older "resource exhaustion" model.** A backgrounded game causes system-wide mouse lag
via two load-independent mechanisms, even at low load (20 cores, 36GB free, idle swap, GPU 6%):
1. **Priority inversion on the input path** — a game at `NI -5` (boosted below normal) is scheduled
   ahead of KWin's input thread on contention; its wakeups widen scheduler jitter system-wide.
2. **Compositor present queue / zombie-window cliff (~3ms LDAT)** — a non-occluded, non-minimized
   backgrounded game keeps submitting GPU presents, shrinking KWin's serial composite schedule for
   every other client including the pointer.

**Memory/TLB are red herrings** when RAM is free: no reclaim, DRAM bandwidth far from saturated,
TLB is per-core (no cross-core pollution), cost is nanoseconds, THP `[always]` already compresses it.

Diagnosis: `ps -eo pid,comm,%cpu,pri,ni --sort=-%cpu | head` — look for boosted (NI negative) game
threads; check if a game presents while unfocused.

Fixes (global): raise the game's nice above normal (`nice 10` or GameMode `gamemoderun %command%`),
minimize/move-to-other-virtual-desktop when unfocused (LDAT-verified biggest win), strict MangoHud
`fps_limit`, `LatencyPolicy=LatencyLow` + `KWIN_DRM_OVERRIDE_SAFETY_MARGIN=-150`.

Brain node: `background_game_mouse_lag_priority_compositor`.

## Process
1. **Audit current state first** — GRUB cmdline, CPU governor, C-states, USB HID polling, MOUSE_POLL, KWin compositing, sysctl, NVIDIA state, services (PPD, keyd, irqbalance), hugepages, env vars.
2. **Check ALL before proposing** — never guess. Run `cat /proc/cmdline`, `libinput list-devices`, `sysctl <param>`, `nvidia-smi` etc.
3. **Fix one layer at a time**, verify each.
4. **Permanent fixes only** — no temporary tests unless user agrees.

## GRUB Kernel Parameters
Add to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`:
```
preempt=full threadirqs
cpufreq.default_governor=performance intel_pstate=active
usbhid.mousepoll=1 usbhid.kbpoll=1
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40
usbcore.autosuspend=-1
intel_idle.max_cstate=1 processor.max_cstate=1
hugepagesz=2M hugepages=2048
transparent_hugepage=madvise
pcie_aspm.policy=performance pci=pcie_bus_perf pcie_ports=native
vdso=2 skew_tick=1 futex_waitv=1
workqueue.power_efficient=false
nvidia_drm.modeset=1 nvidia_drm.fbdev=1
```
Then `sudo grub-mkconfig -o /boot/grub/grub.cfg` and reboot.

## Kernel 7.0+ Epochal Changes

Linux 7.0 (April 2026) and 7.1 (June 2026) introduced structural changes that affect latency tuning strategy. Apply these to the GRUB parameter set above and the assessment sections below.

### Preemption Model Restriction (7.0)
The kernel now restricts preemption models to **Full** and **Lazy** only — `voluntary` and `basic` preemption modes are dropped (Peter Zijlstra, sched/core branch). The `preempt=full` parameter is still valid and remains the correct choice for desktop latency. Lazy preemption is a new hybrid: most kernel code is preemptible (like full) but RCU read-side critical sections are not, trading a small amount of preemption latency for throughput in RCU-heavy workloads.

### Intel FRED Enabled by Default (7.1)
Flexible Return and Event Delivery is an architectural rework of CPU exception/interrupt delivery on Panther Lake+ and newer Intel platforms. FRED reduces interrupt handling overhead by redesigning the low-level transition path. Enabled by default on supported hardware in 7.1. Systems on older Intel simply ignore the feature — no regression. For Panther Lake+ systems, this is a free latency reduction in interrupt-heavy workloads (networking, real-time audio, high-rate I/O).

### sched_ext Sub-Schedulers (7.1)
Linux 7.1 adds sub-scheduler support in the sched_ext (SCX) framework, allowing multiple scheduler policies to coexist in the same kernel build. For desktop tuning, this means BPF-based schedulers like `scx_lavd` (latency-aware), `scx_bpfland` (fair + latency-sensitive), and `scx_rusty` can be loaded at runtime without kernel rebuild. The `BORE` scheduler (CachyOS default) continues to work on 7.x.

### NTSYNC Driver (stabilized in 7.0)
Windows NT synchronization primitives (mutexes, semaphores, events) are now implemented in-kernel for Wine/Proton. Previously emulated in userspace, this eliminates significant CPU overhead in heavily threaded games. GamingOnLinux benchmarks show 15-25% FPS improvement in Cyberpunk 2077 and Microsoft Flight Simulator on kernel 7.0. Verify: `lsmod | grep ntsync`.

### DRM Scheduler Patches (in 7.2 pipeline)
Patches to the kernel's Direct Rendering Manager scheduler show much lower GPU job submission latency when the system is loaded with many runnable CPU processes (Phoronix, July 2026).

### "Flatten the Pick" Scheduler Patches (queued for 7.3)
Improves gaming performance on older hardware via better cgroup scheduling for latency-sensitive tasks (Phoronix, July 2026).

### intel_pstate HWP Mode — Sysfs Lock on `active`

On kernel 7.0+ with `intel_pstate=active` (HWP mode) on modern Intel (Arrow Lake / Ultra 200), the `energy_performance_preference` sysfs is **read-only**. Writing `performance` produces `Device or resource busy`. This is expected — HWP firmware manages EPP directly. The correct tuning approach is `min_perf_pct` via `/sys/devices/system/cpu/intel_pstate/min_perf_pct`, which prevents the CPU from dropping into deep frequency floors. Default `min_perf_pct=25` lets the CPU hit 800 MHz idle; raising to 70 keeps the floor at ~3-4 GHz.

**Key pitfalls:** `hwp_dynamic_boost` can be inadvertently cleared when poking at intel_pstate sysfs. Always verify and restore it after any tuning session.

See `references/intel-pstate-hwp-tuning.md` for full details, the systemd service unit, and resume hook fragment.

### PREEMPT_RT Maturity
Most of PREEMPT_RT is now merged mainline (as of kernel 6.x). The remaining out-of-tree patches include i915 DRM graphics driver adjustments, with ongoing work to make Intel graphics code play nicely with real-time Linux (Phoronix, July 2026). For desktop IRQ thread priority: assign timer IRQ threads priority 80, network 50, storage 30. Lock memory with `mlockall(MCL_CURRENT | MCL_FUTURE)` in latency-sensitive applications.

### Removed/Deprecated in 7.x
- `intel_idle/max_cstate` sysfs path does not exist on 7.0+ — use GRUB `processor.max_cstate=1` instead
- Intel i486 sub-architecture support removed in 7.1 (140K+ lines of dead code)
- UDP Lite support removed in 7.1
- IPv6 can no longer be compiled as a loadable module (`CONFIG_IPV6=m` must become `=y` or `=n`)

## USB hwdb 1000Hz Polling
File: `/etc/udev/hwdb.d/71-corsair-polling.hwdb`
```
evdev:input:b*v1B1Cp1BAC* MOUSE_POLL=1
evdev:input:b*v331Ap5020* MOUSE_POLL=1
```
Apply: `sudo systemd-hwdb update && sudo udevadm trigger`

## Sysctl Workstation
File: `/etc/sysctl.d/99-workstation.conf`
```
vm.swappiness = 5
vm.dirty_ratio = 5
vm.dirty_background_ratio = 2
vm.page-cluster = 0
kernel.hung_task_timeout_secs = 0
kernel.sched_rt_runtime_us = -1
```
Apply: `sudo sysctl --system`

## zram / Swap Pressure (silent stutter source on 64GB systems)

CachyOS/Arch ship **zram-generator** plus a udev rule (`/usr/lib/udev/rules.d/30-zram.rules`) that forces `vm.swappiness=150`. On RAM-rich systems this actively hurts: the kernel pushes idle AND game pages into compressed swap for no reason → stutter. Real case: Dota2 had 1.25 GB in zram while 38 GB RAM was free; 8 GB total had been swapped. On 64 GB, zram has no point — it's a distro default for small-RAM machines.

Diagnosis:
```bash
swapon --show                      # zram0 present? how much used?
cat /proc/sys/vm/swappiness        # 150 => zram udev rule active
grep -rn 'SYSCTL{' /etc/udev/rules.d/ /usr/lib/udev/rules.d/   # find the writer
```

**Why the value "flips back" to 150:** udev loads rules only at EVENT time. Editing/replacing a rule file does nothing until `udevadm control --reload` AND a new matching event fires. The boot-time zram event already ran with the old rule, so the value stays 150. Worse, a bare `udevadm trigger` re-fires the file CURRENTLY installed — if the original 150 rule still exists, trigger re-applies 150. Fix order matters.

Permanent fix (shadow the rule + kill the generator):
```bash
# 1. Shadow the 150 rule with the same filename (later lexicographic order wins)
sudo tee /etc/udev/rules.d/30-zram.rules <<'EOF'
ACTION=="change", KERNEL=="zram0", ATTR{initstate}=="1", SYSCTL{vm.swappiness}="10"
EOF
sudo udevadm control --reload
# 2. Remove zram from swap and stop it permanently
sudo swapoff /dev/zram0
sudo systemctl mask systemd-zram-setup@zram0.service
sudo touch /etc/systemd/zram-generator.conf   # CRITICAL: empty /etc file overrides /usr/lib
#    Without this the generator recreates zram+swap at next boot — disable alone is NOT enough
```
Verify next boot: `swapon --show` shows only the disk partition; `ls /run/systemd/generator/ | grep zram` is empty.

See `references/zram-swap-audit.md` for the full diagnosis transcript and the udev/sysctl broken-rule tables.

## KWin Compositor

### Settings
File: `~/.config/kwinrc` → `[Compositing]`
```
Enabled=false
LatencyPolicy=LatencyLow
AnimationSpeed=0
MaxFps=165
GLVSync=never
```

### Deep Latency Analysis (farnoy.dev, 2026-06)
LDAT-measured click-to-photon latency on KDE Wayland 6.6.4 + NVIDIA 595.58.03 + Zen 4 revealed three structural latency sources in KWin:

1. **Render Journal Overestimation** — KWin predicts ~11ms compositing time but actual GPU work is ~2ms. The ~9ms delta is budgeted as "room for other clients" + safety margin + timer slack. This directly inflates input-to-present latency in windowed apps.

2. **2ms GPU Render Time Floor** — Hardcoded in `src/opengl/glrendertimequery.cpp`. KWin's RenderJournal decays toward 2ms even on a 4090 where p50 GPU compositing is 0.36ms. On idle desktops, this floor dominates the prediction. Fix: use p95 of last 512 frame measurements instead of a hard floor.

3. **1ms Timer Slack** — Qt's QBasicTimer rounds durations to the next millisecond on Unix (`src/corelib/kernel/qtimerinfo_unix.cpp` line 249). At 120Hz (8.3ms frame), 1ms is 12% of the budget. At 360Hz (2.78ms), it's 36%. Replacing with timerfd + QSocketNotifier achieved 51us p99 wakeup deviation.

### Safety Margin Override (NVIDIA-specific)
KWin applies a configurable safety margin to DRM commit timing:
```bash
# Override safety margin in microseconds (can be negative)
# Default: 1000 (1ms). Lower = less slack, tighter latency.
# On NVIDIA 595+ with modern kernel, -150 to 0 is feasible.
export KWIN_DRM_OVERRIDE_SAFETY_MARGIN=-150
```
Add to `/etc/environment.d/99-nvidia-wayland.conf` or `~/.config/environment.d/kwin.conf`.

### Profiling KWin's Performance
Built-in — no patching required:
```bash
# Captures compositing timing data to CSV
KWIN_LOG_PERFORMANCE_DATA=1 kwin_wayland --replace &
# Output: ~/kwin perf statistics <output>.csv
# Analyze with miller:
mlr --c2m rename -g -r ' ,_' then \
  stats1 -f predicted_render_time,render_time,safety_margin -a p50,p75,p95 \
  "kwin perf statistics HDMI-A-1.csv"
```

### Game-Side Latency Fixes (from LDAT measurements)
Measured across Doom Eternal (Vulkan), Borderlands 3 (DX11/DX12), Hades 2 (DX12):

1. **PROTON_ENABLE_WAYLAND=1** — Bypasses XWayland entirely. Without this, XWayland's buffer queue causes extra frames of latency when FPS matches refresh rate with V-Sync. This was the single biggest latency win across all tested titles.

2. **Late FPS limiting via MangoHud** — Cap 2-3 FPS below refresh rate (e.g., 117 on 120Hz). Prevents queue buildup at the V-Sync boundary.

3. **VKD3D_SWAPCHAIN_LATENCY_FRAMES=1** — For DX12 games, reduces swapchain buffer count. Note: with wine_wayland at fixed refresh this caps frame rate at half refresh — only use with FPS cap below that boundary.

4. **DXVK_CONFIG="d3d9.maxFrameLatency=1;dxgi.maxFrameLatency=1"** — Minimal measurable impact on DXVK 2.x+ (already manages latency well).

5. **VRR itself had no significant latency impact** in measured tests.

### Zombie Window Latency Cliff
An idle app that presents every frame (eglgears, Zed editor, Chromium with animations) keeps KWin fully occupied, shrinking the scheduling window for other clients. LDAT confirmed: open Zed editor added ~3ms to all other windowed apps. Fix: minimize or move high-frame-rate windows to a separate virtual desktop.

### What's Coming Upstream
- `commit-timing` in KWin (MR !8955)
- wl_shm speed improvements (zamundaaa.github.io, 2026-05)
- Vulkan-based compositing in KWin 6.8 (dropping Desktop OpenGL per Phoronix, July 2026)
- `VK_EXT_present_timing` for integer-divisor FPS capping

## System-wide NVIDIA Wayland Env
File: `/etc/environment.d/99-nvidia-wayland.conf`
```
WLR_NO_HARDWARE_CURSORS=1
GBM_BACKEND=nvidia-drm
__GL_SYNC_TO_VBLANK=0
__GLX_VENDOR_LIBRARY_NAME=nvidia
QT_QPA_PLATFORM=wayland
XDG_SESSION_TYPE=wayland
```

## Resume Hook (CRITICAL: argument order)
File: `/usr/lib/systemd/system-sleep/latency-fix` | Template: `references/resume-hook-template.sh`
- **Must use `case "$1" in post)`** — NOT `$2`. First arg = phase (pre/post), second = sleep type (suspend/hibernate). A hook using `$2` runs on wake but does NOTHING because "suspend"/"hibernate" never equals "post".
- Runs as root automatically on every wake.
- Actions: re-trigger udev input, NVIDIA max perf, CPU performance + intel_pstate persistence, sysctl, hugepages with compact_memory + stepped alloc, KWin restart, display mode reset.
- **Must restore `min_perf_pct` and `hwp_dynamic_boost`** after sleep — these intel_pstate sysfs values do NOT survive S3.
- **Hugepage loop must use `-ge` guard**: `[ "$CURRENT" -ge 2048 ] && break` — using `[ "$CURRENT" = "$pages" ]` breaks at the first step (512) and never reaches the target of 2048.
- Remove the `echo 1 > /sys/devices/system/cpu/intel_idle/max_cstate` line — the path does NOT exist on kernel 7.0+. C-states locked via GRUB already.

## Hugepages After Sleep
- Boot alloc works (2048 pages on this system). After S3 sleep, memory fragments and alloc may drop to 512.
- Fix: `echo 1 > /proc/sys/vm/compact_memory` then stepped allocation (512→1024→1536→2048).
- **Critical guard**: the loop must use `[ "$CURRENT" -ge 2048 ] && break` NOT `[ "$CURRENT" = "$pages" ] && break`. The `= $pages` form breaks immediately at 512 because the first step succeeds, never reaching the target 2048. This is a confirmed bug in the original post-resume hook.
- 512 pages (1GB) is sufficient for desktop TLB coverage, but some workloads (VM, audio) target 2048 (4GB). The stepped loop handles both cases.

## Disable Mouse Acceleration (KDE Wayland)
- **See also: `references/dbus-mouse-acceleration.md`** for full DBus command reference and device-finding scripts.
- **Do NOT use libinput quirks file** — `AccelProfile=Flat` is NOT a valid quirk property and causes libinput errors.
- **Critical: `libinput list-devices` shows DEFAULTS, not KWin's runtime settings.** The `*adaptive` you see means nothing about what KWin is actually using. The real state is on DBus.
- **Check ACTUAL acceleration state via DBus** (the only reliable way on Wayland):
  ```bash
  # Find the Corsair mouse event (changes on replug!)
  for ev in /org/kde/KWin/InputDevice/event*; do
    NAME=$(dbus-send --session --dest=org.kde.KWin --print-reply $ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"name" 2>&1 | grep -o '"Corsair.*"' | tr -d '"')
    [ -n "$NAME" ] && echo "$ev: $NAME"
  done
  # Then check:
  dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/event<N> org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileFlat"
  ```
- **Set flat via DBus (applies instantly, no logout):**
  ```bash
  dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/event<N> org.freedesktop.DBus.Properties.Set string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileFlat" variant:boolean:true
  dbus-send --session --dest=org.kde.KWin --print-reply /org/kde/KWin/InputDevice/event<N> org.freedesktop.DBus.Properties.Set string:"org.kde.KWin.InputDevice" string:"pointerAcceleration" variant:double:0.0
  ```
- **KDE config backup approach** (for persistence across reboots):
  1. Delete any per-device `[Libinput][...][Corsair...]` section from `~/.config/kcminputrc`
  2. Set global Mouse section: `XLbInptAccelProfileFlat=true`, `AccelerationProfile=0`, `PointerAcceleration=0`
  3. Remove any invalid `/etc/libinput/local-overrides.quirks` file (it breaks libinput)
- **Event numbers change on replug/logout** — always re-find the device path on DBus before setting properties.

## Services to Disable
- `sudo systemctl disable --now power-profiles-daemon`
- `systemctl --user mask keyd`

## Chrome on NVIDIA Wayland
Use native EGL instead of ANGLE for lower latency:
```
google-chrome-stable --use-gl=egl --ozone-platform=wayland
```

## Backup / Redeploy of the Tuning Stack

Every file this skill tunes (`/etc/sysctl.d/*`, `/lib/systemd/system-sleep/latency-fix`, `/usr/local/bin/*`, the cpu0 boot service, `/etc/default/cpupower-service.conf`) is versioned into the dotfiles GitHub repo as a **real-path `system/` mirror** (`~/.dotfiles/system/...` — e.g. `system/lib/systemd/system-sleep/latency-fix`), refreshed on every backup run by `sync_system_files()` in `~/.dotfiles/backup.sh`. A `$HOME`-relative manifest like `dotfiles.txt` can't carry these, hence the mirror + a dedicated restore script.

To (re)deploy the whole stack on a fresh machine AFTER `restore.sh --apply`:
```bash
sudo bash ~/.dotfiles/restore-system.sh   # installs files to /, enables cpu0 boot service,
                                          # reapplies cpu0 HWP + sysctl + IRQ pin + prio guard now
```
`restore.sh --apply` only restores `$HOME` configs — it never touches `/etc`, `/usr`, `/lib`. Always run `restore-system.sh` too.

## Verification Commands

### Standard Checks
```bash
cat /proc/cmdline | tr ' ' '\\n' | grep -E 'preempt|threadirqs|quirks|autosuspend|cstate|huge|performance|poll'
kreadconfig5 --file kwinrc --group Compositing --key Enabled
kreadconfig5 --file kwinrc --group Compositing --key LatencyPolicy
cat /sys/module/usbhid/parameters/mousepoll
cat /sys/module/usbhid/parameters/quirks
udevadm info /dev/input/by-id/usb-Corsair* 2>&1 | grep MOUSE_POLL
sudo libinput list-devices 2>&1 | grep -A 30 'Corsair.*Mouse' | grep Accel
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
grep HugePages_Total /proc/meminfo
sysctl kernel.sched_rt_runtime_us
systemctl is-active power-profiles-daemon
journalctl -b | grep 'latency-fix'
echo $KWIN_DRM_OVERRIDE_SAFETY_MARGIN
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct
cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost
lsmod | grep ntsync
# KWin perf profiling (run, then capture CSV):
KWIN_LOG_PERFORMANCE_DATA=1 kwin_wayland --replace 2>&1 &
# then: mlr --c2m rename -g -r ' ,_' stats1 -f predicted_render_time,render_time,safety_margin -a p50,p75,p95 '~/kwin perf statistics *.csv'
```

### Env Var Loading Verification

Env vars set in `~/.config/environment.d/*.conf` are loaded by systemd at session start, but may NOT be loaded if the file was created or modified after login. Always verify what's actually running:

```bash
# What systemd thinks it loaded (session-level env)
systemctl --user show-environment 2>/dev/null | grep -E 'KWIN_DRM|__GL|KWIN_TRIPLE'

# What KWin actually inherited (may differ if KWin started before env.d file existed)
cat /proc/$(pgrep kwin_wayland | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep -E 'KWIN_DRM|KWIN_TRIPLE|__GL_MaxFrames|__GL_SYNC'

# What the current shell sees (may differ from both of the above)
echo $KWIN_DRM_OVERRIDE_SAFETY_MARGIN
```

**Common pitfall:** Variable set in a later-added `99-kwin.conf` but absent from both `systemctl --user show-environment` and `/proc/kwin_wayland/environ` — file was added after session start and KWin was never restarted. Fix:
```bash
systemctl --user import-environment
systemctl --user restart plasma-kwin_wayland.service
```
Or full logout/login.

### VRR Diagnostic On/Off

VRR (AdaptiveSync) on NVIDIA Wayland can cause input lag. Test with it off — works instantly, no restart:
```bash
kscreen-doctor output.DP-3.vrr.off   # instant toggle, test feel
kscreen-doctor output.DP-3.vrr.on    # restore
```
If VRR off fixes the lag, disable permanently in kwinrc: `VrrPolicy=Never`.

## Config Conflict Detection

PipeWire has **three config layers** that act independently and silently override each other:

| Layer | Directory | Files |
|-------|-----------|-------|
| Core PW config | `~/.config/pipewire/pipewire.conf.d/` | Sets `clock.quantum`, `clock.min-quantum`, `clock.force-quantum` |
| Pulse compat config | `~/.config/pipewire/pipewire-pulse.conf.d/` | Sets `default.clock.quantum` (pulse-only path) |
| ALSA sink adapter | `~/.config/pipewire/pipewire.conf.d/` per-sink file | Sets `api.alsa.period-size` (hardware-side, can differ from graph quantum) |

**Diagnosis commands:**
```bash
pw-metadata -n settings | grep quantum
# Shows what's actually running — may differ from ALL config files

# Find ALL config files setting quantum/period values
grep -rn 'quantum\|period-size\|force.quantum' \
  ~/.config/pipewire/ /etc/pipewire/ 2>/dev/null | grep -v '^\s*#'
```

**When the running `force-quantum` disagrees with `alsa-sink`'s `period-size`**, the graph processes at the forced quantum but the hardware peripheral doubles/halves internally. This wastes the ALSA buffer tuning. Align all configs to the same quantum.

Also scan for cross-layer env var conflicts:
```bash
# Find ALL files setting the same KWIN/__GL/etc variable
grep -rn 'KWIN_DRM_OVERRIDE\|KWIN_DRM_ALLOW\|__GL_SYNC\|__GL_MaxFrames\|KWIN_DRM_DISABLE' \
  /etc/environment ~/.config/environment.d/ /etc/environment.d/ 2>/dev/null | grep -v '^\s*#'
```

## GRUB Parameter Concatenation Bug

**The problem:** When editing `GRUB_CMDLINE_LINUX_DEFAULT`, two adjacent parameters can merge into one if there is no whitespace between them. The shell's string concatenation in the single-quoted GRUB variable doesn't warn — the merged string is passed to the kernel verbatim, which treats it as an invalid value and silently falls back to the default.

**Example failure:**
```ini
# Intent: two separate params
pcie_aspm.policy=performance sched_itmt_enabled=1

# What the GRUB line actually has (no space):
pcie_aspm.policy=performancesched_itmt_enabled=1
```
Result: `pcie_aspm.policy` receives `performancesched_itmt_enabled=1` (invalid → kernel uses `default` policy). `sched_itmt_enabled=1` is never parsed.

**Check for it:**
```bash
grep 'pcie_aspm.policy=' /proc/cmdline | grep -q 'performance ' || echo "WARNING: pcie_aspm.policy=performance may be merged into another param"
```

**Root cause:** The `GRUB_CMDLINE_LINUX_DEFAULT` line is a single long string — every param boundary must have a space. A common trigger: moving a parameter next to another during editing without verifying the space is preserved.

**Fix:**
```bash
# Verify the current /etc/default/grub line has proper spacing
grep -o 'pcie_aspm.policy=performance' /etc/default/grub

# Fix merged parameters — edit /etc/default/grub and add the missing space
sudo sed -i 's/pcie_aspm.policy=performancesched_itmt_enabled=1/pcie_aspm.policy=performance sched_itmt_enabled=1/' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

Then verify after reboot:
```bash
cat /sys/module/pcie_aspm/parameters/policy
# Should show: [performance] default powersave powersupersave
```

## Full Config Enumeration for Comprehensive Audit

When the user asks about "all system configs" or expresses frustration with layered/round-based output, dump EVERYTHING at once. Run these in parallel batches:

### Batch 1 — Boot + Kernel
```bash
cat /proc/cmdline | tr ' ' '\n'
cat /proc/version
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
zcat /proc/config.gz 2>/dev/null | grep -E 'PREEMPT|HZ_' | head -10
cat /sys/module/pcie_aspm/parameters/policy
```

### Batch 2 — GPU + Driver
```bash
nvidia-smi --query-gpu=name,driver_version,pcie.link.gen.current,pcie.link.width.current,power.limit --format=csv,noheader
cat /etc/modprobe.d/nvidia*.conf 2>/dev/null
```

### Batch 3 — Config Files (enumerate ALL)
```bash
config_files=(
  /etc/default/grub
  /etc/sysctl.d/*.conf
  /etc/udev/rules.d/*.rules
  /etc/udev/hwdb.d/*.hwdb
  /etc/modprobe.d/*.conf
  /etc/environment
  /etc/environment.d/*.conf
  ~/.config/environment.d/*.conf
  ~/.config/kwinrc
  ~/.config/pipewire/*.conf
  ~/.config/pipewire/pipewire.conf.d/*.conf
  ~/.config/pipewire/pipewire-pulse.conf.d/*.conf
  /etc/security/limits.d/*.conf
  /etc/systemd/system/*.service
  /etc/systemd/system/*.service.d/*.conf
  /usr/lib/systemd/system-sleep/*
  /etc/pipewire/*.conf
  /etc/pipewire/*.conf.d/*.conf
)
for f in "${config_files[@]}"; do
  [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo
done
```

### Batch 4 — Running State
```bash
sysctl vm.swappiness vm.dirty_ratio vm.dirty_background_ratio vm.page-cluster kernel.sched_rt_runtime_us
cat /sys/module/usbhid/parameters/mousepoll
cat /sys/module/usbhid/parameters/kbpoll
cat /sys/module/usbhid/parameters/quirks
pw-metadata -n settings 2>/dev/null
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct
cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost
cat /sys/kernel/mm/transparent_hugepage/enabled
grep HugePages_Total /proc/meminfo
pgrep keyd && echo "keyd running (should not be)" || echo "keyd not running (good)"
```

### Batch 5 — IRQ Distribution
```bash
cat /proc/interrupts | grep -E 'nvidia|xhci_hcd|nvme|iwlwifi|snd_hda|igc'
```
Check for GPU vs USB IRQs on the same CPU.

This comprehensive approach matches the user's expectation of "give me everything at once" rather than layering findings round by round.

## Common Pitfalls
- **Zombie window latency cliff**: An idle app presenting every frame (Zed editor, eglgears, Chromium with animations) keeps KWin fully occupied, shrinking the scheduling window for all other clients. LDAT confirmed ~3ms added latency to windowed apps. Fix: minimize high-frame-rate windows to a different virtual desktop. Detected via bpftrace: `@mode_atomic` commit calls == refresh rate.
- **KWIN_DRM_OVERRIDE_SAFETY_MARGIN**: Negative values are accepted and work but reduce effective safety margin. The adaptive `m_additionalSafetyMargin` may not compensate as expected. Start at -150 and monitor for slipped frames using the perf profiler.
- **PROTON_ENABLE_WAYLAND=1**: Required per-game env var. Without it, games run through XWayland which adds buffer queue latency when FPS matches refresh rate with V-Sync. This was the single biggest latency win across all LDAT-measured titles (farnoy.dev, 2026-06).
- **Resume hook `$1` vs `$2`**: `case "$1" in post)` is correct — checking `$2` (suspend type like "suspend") means the hook silently never fires. This is the #1 cause of "hook installed but not working" — logger shows no output, everything looks correct, hook simply wasn't reached.
- **`kernel.sched_rt_runtime_us` defaults to 950000**: On Manjaro/Arch, the kernel caps RT threads at 95% CPU time. With `threadirqs`, USB/keyboard/mouse interrupt threads get forcibly preempted for 50ms every second — causing periodic input lag spikes. Fix: `sysctl kernel.sched_rt_runtime_us=-1` and add to `/etc/sysctl.d/99-workstation.conf`. Apply with `sudo sysctl --system`.
- **`intel_idle/max_cstate` sysfs**: Does not exist on kernel 7.0. Use GRUB `processor.max_cstate=1` instead. Remove any `echo 1 > /sys/devices/system/cpu/intel_idle/max_cstate` from resume hooks.
- **`nvidia-smi -frl`**: Not a valid flag on driver 595+. Use `nvidia-smi -pm 1` instead.
- **`nvidia-smi -acp ULTRA`**: Not available on some driver versions. Skip this flag entirely.
- **nvidia-settings on Wayland**: `GPUPowerMizerMode=1` works when called from the user session with the display context. But `CurrentMetaMode`, `ColorSpace`, `ColorRange` queries fail on Wayland — use `kscreen-doctor -o` for display state instead.
- **Libinput quirks**: `AccelProfile=Flat` is NOT a valid quirk property. An invalid quirks file (`/etc/libinput/local-overrides.quirks`) causes libinput to print "Unknown value prefix" errors and fail loading ALL quirks for ALL devices — making input worse. Remove invalid files immediately.
- **`libinput list-devices` shows defaults, not KWin runtime**: The `*adaptive` asterisk is the libinput library DEFAULT, NOT what KWin's compositor context is using. Check the real profile via DBus at `/org/kde/KWin/InputDevice/event<N>` using `pointerAccelerationProfileFlat` property.
- **Event numbers change on replug/logout**: The `/dev/input/event<N>` number shifts when a USB device reconnects. Always re-find the correct event number by scanning DBus device names before querying input properties.
- **Hugepage GRUB param**: `nr_hugepages=N` may be treated as "Unknown kernel command line parameter" on some kernels (7.0). Use `hugepages=N` instead. Runtime allocation via `/sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages` always works regardless.
- **hwp_dynamic_boost cleared by EPP sysfs writes**: Writing to `energy_performance_preference` on `intel_pstate=active` (even when it fails with "Device or resource busy") can clear `hwp_dynamic_boost` from 1 to 0. Always verify and restore after tuning. Check: `cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost`. Restore: `echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost`.\n- **Hugepage resume loop early-break bug**: Using `[ "$CURRENT" = "$pages" ] && break` in the stepped allocation loop (512→1024→1536→2048) breaks at 512 because the first step succeeds. Must use `[ "$CURRENT" -ge 2048 ] && break` to reach the target.\n- **min_perf_pct and hwp_dynamic_boost lost on sleep**: These intel_pstate sysfs values do NOT survive S3. The resume hook must explicitly restore them. Verify after resume: `cat /sys/devices/system/cpu/intel_pstate/min_perf_pct` (should be 70, not 25) and `cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost` (should be 1).\n- **Sudo caching**: Password expires regularly. Write scripts to `~/*.sh` for the user to run, rather than expecting sustained sudo access.
- **Post-sleep xHCI error**: Gigabyte Z890 shows `xHC error in resume, USBSTS 0x401`. The resume hook compensates with `udevadm trigger --subsystem-match=input` to re-apply hwdb/MOUSE_POLL after the xHC reinit.
- **NVIDIA IRQs pinned to CPU0 by default**: On kernel 7.0 + NVIDIA 595+, all 6 MSI-X vectors (IRQ 147-152) can have `effective_affinity=00001` (CPU0) even when `smp_affinity` is set to a wider mask (`000ff`, `003ff`, etc.). ALL GPU interrupt load lands on a single core. Writing to `smp_affinity_list` overrides this directly — unlike `smp_affinity` (hex mask), `smp_affinity_list` takes decimal CPU numbers and directly updates the kernel's IRQ dispatch table. The `pin-irqs-dynamic` script in `linux-performance-tuning` handles this. After resume, NVIDIA reinitializes and resets IRQ affinity back to CPU0 — the resume hook must re-pin after the NVIDIA PM step.
- **GRUB parameter concatenation**: The `GRUB_CMDLINE_LINUX_DEFAULT` line is a single string. Missing a space between two adjacent params merges them into one invalid parameter. This silently falls back to the default, not a visible error. Always verify spacing around every parameter boundary after editing `GRUB_CMDLINE_LINUX_DEFAULT`. Check with `cat /sys/module/pcie_aspm/parameters/policy` (should show `[performance]`). Fix: `sudo sed -i 's/bad_merged_params/good spaced params/' /etc/default/grub && sudo grub-mkconfig -o /boot/grub/grub.cfg`.
- **PipeWire config conflicts across multiple directories**: `~/.config/pipewire/pipewire.conf.d/`, `~/.config/pipewire/pipewire-pulse.conf.d/`, and `~/.config/pipewire/` can all set different `quantum`, `min-quantum`, and `force-quantum` values. The `force-quantum` in `pipewire.conf.d/` overrides everything else. Always check ALL directories for conflicting values using `grep -rn 'quantum\|period-size\|force.quantum' ~/.config/pipewire/ /etc/pipewire/ 2>/dev/null | grep -v '^\s*#'` and `pw-metadata -n settings | grep quantum`.
- **NVMe power control defaults to `auto`**: Both NVMe drives have `power/control=auto`, permitting power state transitions (PS2/PS3 → PS0) on every I/O. On a latency-tuned system, set to `on` via udev rule or manually: `for d in /sys/bus/pci/devices/*/nvme/nvme*/power/control; do echo on > "$d" 2>/dev/null; done`. Check current state: `find /sys/devices/pci* -name "nvme*" -type d 2>/dev/null | while read nvme; do echo "$nvme: power/control=$(cat $nvme/power/control 2>/dev/null)"; done`.

- **zram-generator recreates zram at every boot**: `systemctl disable systemd-zram-setup@zram0.service` is NOT enough — the generator reads `/usr/lib/systemd/zram-generator.conf` (CachyOS: zram-size=ram) and recreates the device + swap each boot. The permanent kill is `touch /etc/systemd/zram-generator.conf` (empty /etc config overrides /usr/lib) + `systemctl mask systemd-zram-setup@zram0.service` + `swapoff /dev/zram0`. Verify after reboot: `swapon --show` shows only the disk partition.
- **udev rules only apply at event time**: Editing/replacing a rule file does NOT apply it. You need `sudo udevadm control --reload` AND a new matching udev event. A bare `udevadm trigger` re-fires whatever rule files are CURRENTLY installed — so if the original 150-swappiness rule still exists, trigger re-applies 150. This is why "I changed the rule but the value is still 150".
- **NVMe udev rules must match the namespace, not the controller**: `KERNEL=="nvme[0-9]*"` matches `nvme0` (the controller), which has NO `queue/scheduler` or `queue/read_ahead_kb` → "Could not chase sysfs attribute" error every boot, rule silently does nothing. Use `KERNEL=="nvme[0-9]n[0-9]*"` (e.g. `nvme0n1`). Detect broken rules: `journalctl -b | grep 'udev-worker.*Could not chase'` and aggregate by `rules.d/<file>:<line>`.
- **sysctl.d later-file-wins (silent overrides)**: Files in `/etc/sysctl.d/` override lexicographically — the LAST file alphabetically wins per key, regardless of intent. Always check the runtime value vs ALL files, not just the file you think sets it. Real cases: `99-workstation.conf` (vfs_cache_pressure=100) silently overrode `99-performance.conf` (50); `99-performance.conf` (max_map_count=262144) overrode Manjaro's `10-manjaro.conf` (1048576). Verify: `sysctl <key>` then `grep -rn '<key>' /etc/sysctl.d/`.
- **Dead sysctl keys on kernel 7.x (EEVDF)**: `kernel.sched_child_runs_first` and `kernel.pressure_stall.max_*` no longer exist — writes fail with "No such file or directory" and are harmless log noise. Remove from sysctl.d to silence.
- **kernel.watchdog=0 removes the last per-core wakeup**: with nmi_watchdog already 0, the softlockup watchdog threads still wake every core periodically (watchdog_cpumask=0-19). `kernel.watchdog=0` kills those too — trade-off is losing softlockup detection, acceptable on a gaming desktop.
- **net.core.netdev_budget_usecs=4000 is 2x default**: network softirq may hog 4ms per round on the NIC's IRQ CPU. Harmless for USB input (hardirqs preempt softirqs) but on online games it can delay the game thread if it shares the NIC's core. Default 2000; tighten if NIC IRQs share cores with the game.
- **tmpfiles.d can't tune cpufreq — it runs before the sysfs nodes exist**: `/etc/tmpfiles.d/10-gaming-cpu.conf` writing `scaling_governor`/`energy_performance_preference` is a silent no-op (nodes absent at tmpfiles time; EPP also gets `-EBUSY` under HWP). Audit: dead tuning configs accumulate silently. Check for them with `systemd-tmpfiles --create --dry-run` or just verify whether the target sysfs actually changed after boot.
- **`net.ipv4.tcp_low_latency=1` is a dead sysctl** — the knob was removed from the kernel years ago; the line in `99-performance.conf` is silently ignored. Before re-proposing any TCP tuning, check the key still exists (`sysctl -a | grep` the key or write it and watch for "unknown key").
- **Resume-hook vs sysctl.d value conflict**: resume hook step 4 set `vm.dirty_ratio=5` on every wake while `99-vm-tune.conf` sets 10 — the value flips between 10 and 5 depending on last suspend. Rule: one owner per tunable. If a sysctl.d file is canonical, the hook must NOT override it; audit hooks against sysctl.d for every key they touch.

## User Preferences (for this system)
- No clarifying questions — give ALL commands immediately. "a" = yes/continue.
- Direct commands, minimal explanation.
- Verify everything after changes — show confirmation output.
- When something fails, provide the fix immediately without apology.
- Expects comprehensive research before any change proposal.
- **NEVER make system-modifying changes without explicit request.** Present findings + exact commands to apply. Let the user decide. This user has expressed extreme frustration when changes were applied without advance consent.
