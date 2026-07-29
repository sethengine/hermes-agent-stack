---
name: linux-system-audit-prompt
description: "Master prompt that forces an LLM to perform a comprehensive Linux system audit — every config, every variable, every kernel param, every service, every IRQ. Cross-references with online research for the latest tweaks. Produces prioritized, manually-executable commands only."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [linux, audit, tuning, prompt, comprehensive]
    related_skills: [linux-performance-tuning, linux-latency-tuning, linux-desktop-performance-audit]
---

# Linux System Audit — Master Prompt

## Purpose

A single paste-in prompt that forces any capable LLM to perform an exhaustive Linux system audit, research current best practices online, and produce a prioritized list of improvements with exact commands — for **manual execution only**.

## The Prompt

Copy everything below the `--- PROMPT START ---` line into a new chat.

---

--- PROMPT START ---

You are performing a COMPREHENSIVE Linux system audit. Your job is to leave NO config unread, NO variable unchecked, NO kernel parameter uninspected. You will research the LATEST online recommendations for this exact hardware and software stack, then produce a prioritized list of improvements with exact copy-paste commands.

## RULES (non-negotiable)

1. **MANUAL EXECUTION ONLY.** You provide commands. The user runs them. You NEVER execute system-modifying commands yourself. Read-only diagnostic commands are fine. Any command that changes state (sysctl, modprobe, systemctl, grub edits, file writes, etc.) — you present for manual review.

2. **INSPECT BEFORE RECOMMENDING.** Never guess. Run the diagnostic command first, see the actual value, THEN compare against best practice. Every recommendation must cite: (a) current measured state, (b) recommended state, (c) why, (d) exact command to apply.

3. **ONLINE RESEARCH REQUIRED.** For every layer below, search the web for current (2026) best practices for this specific hardware + distro + kernel combination. Community recommendations change. Kernel 7.x changed things. Verify.

4. **PRIORITIZE BY IMPACT.** Order findings from highest to lowest real-world impact. Gaming FPS, input latency, desktop responsiveness, audio quality, compile times — in that order for a gaming/workstation hybrid.

5. **NO ROUNDS. ALL AT ONCE.** Dump everything. Every config. Every finding. The user wants comprehensive, not layered.

## THE AUDIT — REQUIRED LAYERS

You MUST run ALL diagnostic commands below. Do not skip layers. Each is independent — run them in parallel batches.

### LAYER 0: System Identity
```bash
uname -a
cat /etc/os-release | head -5
cat /proc/cpuinfo | grep -m1 "model name"
cat /proc/cpuinfo | grep -c "^processor"
lspci | grep -i "vga\|3d\|nvidia"
free -h
lsblk -d -o NAME,SIZE,ROTA,MOUNTPOINT,MODEL
echo $XDG_SESSION_TYPE
echo $DESKTOP_SESSION
```

### LAYER 1: Kernel + Boot
```bash
cat /proc/cmdline | tr ' ' '\n'
cat /proc/version
zcat /proc/config.gz 2>/dev/null | grep -E 'PREEMPT|HZ_|SCHED' | head -15
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq -c
cat /sys/devices/system/cpu/intel_pstate/status 2>/dev/null
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct 2>/dev/null
cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost 2>/dev/null
cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null
cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null
cat /sys/kernel/mm/transparent_hugepage/enabled
cat /sys/kernel/mm/transparent_hugepage/defrag
cat /sys/module/pcie_aspm/parameters/policy
cat /sys/devices/system/cpu/isolated 2>/dev/null
cat /sys/devices/system/cpu/smt/active 2>/dev/null
cat /sys/devices/system/cpu/vulnerabilities/* | head -20
```

### LAYER 2: GPU + NVIDIA Driver
```bash
nvidia-smi --query-gpu=name,driver_version,pcie.link.gen.current,pcie.link.width.current,power.limit,temperature.gpu,utilization.gpu,memory.total,memory.used,clocks.current.sm,clocks.current.memory --format=csv,noheader
nvidia-smi -q | grep -A5 'GSP Firmware'
lsmod | grep -E 'nvidia|nvidia_drm|nvidia_modeset|nvidia_uvm'
cat /sys/module/nvidia_drm/parameters/modeset 2>/dev/null
cat /sys/module/nvidia_drm/parameters/fbdev 2>/dev/null
ls -la /dev/fb* 2>/dev/null
cat /sys/module/nvidia/parameters/NVreg_EnableGpuFirmware 2>/dev/null
ls /lib/firmware/nvidia/ 2>/dev/null | sort
cat /etc/modprobe.d/nvidia*.conf 2>/dev/null
cat /etc/modprobe.d/nvidia-drm.conf 2>/dev/null
ls -la /etc/modprobe.d/ 2>/dev/null
cat /etc/modprobe.d/blacklist*.conf 2>/dev/null
```

### LAYER 3: Wayland + Compositor (KDE)
```bash
grep -A40 '\[Compositing\]' ~/.config/kwinrc 2>/dev/null
grep -A20 '\[Windows\]' ~/.config/kwinrc 2>/dev/null
grep -A20 '\[Effect-overview\]' ~/.config/kwinrc 2>/dev/null
grep -A10 '\[TabBox\]' ~/.config/kwinrc 2>/dev/null
cat ~/.config/kwinrc 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key Enabled 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key LatencyPolicy 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key VrrPolicy 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key MaxFps 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key GLVSync 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key AnimationSpeed 2>/dev/null
kreadconfig5 --file kwinrc --group Compositing --key AllowTearing 2>/dev/null
# Actual running compositor state
qdbus6 org.kde.KWin /Compositor org.freedesktop.DBus.Properties.Get org.kde.kwin.Compositing compositingType 2>/dev/null
kscreen-doctor -o 2>/dev/null
```

### LAYER 4: Environment Variables — EVERY SOURCE
```bash
# System-wide
cat /etc/environment 2>/dev/null
for f in /etc/environment.d/*.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
# User
for f in ~/.config/environment.d/*.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
# Shell
cat ~/.zshrc 2>/dev/null | grep -E 'export |setenv '
cat ~/.profile 2>/dev/null | grep -E 'export |setenv '
# What KWin actually inherited (runtime truth)
cat /proc/$(pgrep kwin_wayland | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep -E 'KWIN_DRM|__GL|KWIN_TRIPLE|GBM_BACKEND|LIBVA|DXVK|VKD3D|PROTON|WLR|QT_QPA|XDG_SESSION|WAYLAND_DISPLAY' | sort
# systemd user environment
systemctl --user show-environment 2>/dev/null | grep -E 'KWIN|__GL|GBM|LIBVA|DXVK|QT' | sort
# Cross-file conflict scan
grep -rn 'KWIN_DRM_OVERRIDE\|KWIN_DRM_ALLOW\|__GL_SYNC\|__GL_MaxFrames\|KWIN_DRM_DISABLE\|KWIN_TRIPLE\|GBM_BACKEND\|LIBVA_DRIVER\|DXVK_\|VKD3D_\|PROTON_ENABLE\|WLR_' /etc/environment ~/.config/environment.d/ /etc/environment.d/ ~/.zshrc ~/.profile 2>/dev/null | grep -v '^\s*#'
```

### LAYER 5: Sysctl + VM + Memory
```bash
sysctl vm.swappiness vm.vfs_cache_pressure vm.dirty_ratio vm.dirty_background_ratio vm.page-cluster vm.watermark_boost_factor vm.watermark_scale_factor
sysctl kernel.sched_min_granularity_ns kernel.sched_wakeup_granularity_ns kernel.sched_latency_ns kernel.sched_rt_runtime_us kernel.sched_autogroup_enabled kernel.hung_task_timeout_secs
sysctl kernel.numa_balancing kernel.randomize_va_space
sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc net.ipv4.tcp_fastopen net.ipv4.tcp_notsent_lowat
grep HugePages_Total /proc/meminfo
grep HugePages_Free /proc/meminfo
grep Hugepagesize /proc/meminfo
cat /proc/meminfo | grep -E 'SwapTotal|SwapFree|SwapCached|Unevictable|Dirty|Writeback'
# All sysctl conf files
for f in /etc/sysctl.d/*.conf /etc/sysctl.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
```

### LAYER 6: Storage + Filesystems
```bash
mount | grep "^/dev/" | awk '{print $1, $3, $5, $6}'
cat /etc/fstab
find /sys/devices/pci* -name "nvme*" -type d 2>/dev/null | while read nvme; do echo "$nvme: power/control=$(cat $nvme/power/control 2>/dev/null)"; done
for nvme in /sys/block/nvme*/queue/scheduler; do echo "$nvme: $(cat $nvme)"; done
df -h | grep -E '^/dev/|Filesystem'
sudo tune2fs -l /dev/nvme*n1p* 2>/dev/null | grep -E "Filesystem state|Errors|Mount count|Last checked"
# Btrfs/ZFS if applicable
btrfs filesystem usage / 2>/dev/null | head -10
zpool status 2>/dev/null
```

### LAYER 7: IRQ Distribution — Critical for Latency
```bash
cat /proc/interrupts | grep -E 'nvidia|xhci_hcd|nvme|iwlwifi|snd_hda|igc|enp'
# Hex-to-CPU mapping for reference
python3 -c "
data = open('/proc/interrupts').read()
for line in data.splitlines():
    if not any(x in line.lower() for x in ['nvidia','nvme','xhci','iwlwifi','snd_hda','igc']):
        continue
    parts = line.split()
    irq = parts[0].rstrip(':')
    if not irq.isdigit(): continue
    aff = open('/proc/irq/%s/smp_affinity' % irq).read().strip()
    eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    ev = int(eff.replace(',',''), 16)
    ec = [i for i in range(64) if ev & (1<<i)]
    lscpu = open('/proc/cpuinfo').read()
    cores = int([l for l in lscpu.splitlines() if '^processor' in l][0].split(':')[1].strip()) if '^processor' in lscpu else 0
    max_cpu = cores
    iso = [c for c in ec if c < 8]
    hk = [c for c in ec if c >= 8]
    if iso and not hk: tag = 'ISOLATED'
    elif iso and hk: tag = 'SPLIT'
    else: tag = 'housekeeping'
    print(f'IRQ {irq:>3} {parts[-1]:20s} aff={aff} eff={eff} CPUs={str(ec):20s} {tag}')
" 2>/dev/null
# Context switch rate
grep "^ctxt" /proc/stat
CTXT1=$(grep "^ctxt" /proc/stat | awk '{print $2}'); sleep 3; CTXT2=$(grep "^ctxt" /proc/stat | awk '{print $2}'); echo "CS/s: $(((CTXT2 - CTXT1) / 3))"
# Top involuntary context switch processes
for pid in $(pgrep -f '' | head -20); do
  [ -f /proc/$pid/status ] && echo "$(cat /proc/$pid/comm 2>/dev/null) ($pid): vol=$(grep voluntary_ctxt_switches /proc/$pid/status 2>/dev/null | awk '{print $2}') nonvol=$(grep nonvoluntary_ctxt_switches /proc/$pid/status 2>/dev/null | awk '{print $2}')"
done 2>/dev/null | sort -t: -k2 -rn | head -15
```

### LAYER 8: USB + Input Latency
```bash
cat /sys/module/usbhid/parameters/mousepoll 2>/dev/null
cat /sys/module/usbhid/parameters/kbpoll 2>/dev/null
cat /sys/module/usbhid/parameters/quirks 2>/dev/null
# USB autosuspend on input devices
for dev in /sys/bus/usb/devices/*/product; do
  [ -f "$dev" ] || continue
  product=$(cat "$dev" 2>/dev/null)
  dir=$(dirname "$dev")
  [ -f "$dir/power/autosuspend" ] && echo "$product: autosuspend=$(cat $dir/power/autosuspend)"
done 2>/dev/null
# hwdb polling overrides
cat /etc/udev/hwdb.d/*.hwdb 2>/dev/null
# WiFi power save
iw dev 2>/dev/null | awk '/Interface/ {print $2}' | while read iface; do
  state=$(iw dev "$iface" get power_save 2>/dev/null)
  echo "$iface: $state"
done
# libinput device list (shows defaults, not runtime)
sudo libinput list-devices 2>/dev/null | grep -A20 'Mouse'
# Actual mouse acceleration via KWin DBus (the real state)
for ev in /org/kde/KWin/InputDevice/event*; do
  NAME=$(dbus-send --session --dest=org.kde.KWin --print-reply $ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"name" 2>&1 | grep -o '".*"' | tr -d '"')
  [ -n "$NAME" ] && echo "$ev: $NAME — flat=$(dbus-send --session --dest=org.kde.KWin --print-reply $ev org.freedesktop.DBus.Properties.Get string:"org.kde.KWin.InputDevice" string:"pointerAccelerationProfileFlat" 2>&1 | grep -o 'true\|false')"
done 2>/dev/null
```

### LAYER 9: Audio — PipeWire
```bash
pw-metadata -n settings 2>/dev/null | grep -E 'quantum|rate'
pactl info 2>/dev/null | grep -E 'Server Name|Default Sink|Default Source'
pactl list sinks short 2>/dev/null
pactl list sink-inputs short 2>/dev/null
# PipeWire config — ALL directories
for d in ~/.config/pipewire /etc/pipewire; do
  find "$d" -name '*.conf' -type f 2>/dev/null | while read f; do
    echo "=== $f ===" && cat "$f" && echo
  done
done
# Check for WirePlumber version (config syntax differs)
wireplumber --version 2>/dev/null
# DMAR faults from NVIDIA HDA audio
dmesg | grep -i 'DMAR.*fault\|INTR-REMAP' | tail -20
# Audio-related loaded modules
lsmod | grep -E 'snd_hda|snd_sof|soundwire'
```

### LAYER 10: Systemd Services + Bloat
```bash
systemctl --failed --no-pager 2>/dev/null
systemd-analyze blame 2>/dev/null | head -15
systemd-analyze critical-chain 2>/dev/null | head -10
systemctl list-units --type=service --state=running | wc -l
systemctl is-active irqbalance 2>/dev/null
systemctl is-active power-profiles-daemon 2>/dev/null
systemctl is-active scx_loader 2>/dev/null
systemctl is-active lactd 2>/dev/null
systemctl is-active bluetooth 2>/dev/null
systemctl is-active cups 2>/dev/null
# sched_ext state
cat /sys/kernel/sched_ext/state 2>/dev/null
# User services
systemctl --user list-units --type=service --state=running | wc -l
# Process count
echo "Total procs: $(ps aux | wc -l) | User: $(ps --User=$(whoami) --no-headers | wc -l) | Chrome: $(ps aux | grep -c '[c]hrome')"
# Coredump waste
sudo du -sh /var/lib/systemd/coredump/ 2>/dev/null
sudo ls /var/lib/systemd/coredump/ 2>/dev/null | wc -l
# LACTD polling config (micro-stutter source)
cat /etc/lact/config.yaml 2>/dev/null | grep -E 'interval_ms|apply_settings_timer'
```

### LAYER 11: Cron + Timers + Hooks
```bash
systemctl list-timers --all 2>/dev/null | head -20
crontab -l 2>/dev/null
sudo crontab -l 2>/dev/null
# systemd-sleep hooks
for f in /usr/lib/systemd/system-sleep/*; do
  [ -f "$f" ] && [ -x "$f" ] && echo "=== $f ===" && cat "$f" && echo
done
# Custom systemd units
for f in /etc/systemd/system/*.service; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo; done
for f in /etc/systemd/system/*.timer; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo; done
# Override files
find /etc/systemd/system/ -name '*.d' -type d 2>/dev/null | while read d; do
  for f in "$d"/*.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo; done
done
```

### LAYER 12: GRUB Config (source of truth)
```bash
cat /etc/default/grub
# Check for parameter concatenation bugs
grep -o 'pcie_aspm.policy=performance' /etc/default/grub
# If on systemd-boot
for f in /boot/loader/entries/*.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f"; done
```

### LAYER 13: Modules — Loaded + Blacklisted
```bash
lsmod | wc -l
lsmod | grep -E 'i915|soundwire|snd_sof|thunderbolt|jfs|hfsplus|hfs|ufs|minix|btusb|bluetooth'
cat /etc/modprobe.d/blacklist*.conf 2>/dev/null
cat /etc/modprobe.d/*.conf 2>/dev/null | grep -i blacklist
# Unused kernel modules loaded for absent hardware
for module in i915 soundwire_intel snd_sof_pci_intel_cnl thunderbolt jfs hfsplus ufs minix; do
  loaded=$(lsmod | grep -c "^$module ")
  [ "$loaded" -gt 0 ] && echo "WARNING: $module loaded but hardware may not exist"
done
```

### LAYER 14: Limits + Security
```bash
ulimit -a 2>/dev/null
cat /etc/security/limits.conf 2>/dev/null | grep -v '^#' | grep -v '^$'
for f in /etc/security/limits.d/*.conf; do [ -f "$f" ] && echo "=== $f ===" && cat "$f" | grep -v '^#' | grep -v '^$'; done
cat /proc/sys/fs/file-max
cat /proc/sys/fs/inotify/max_user_watches
```

### LAYER 15: C-State + Idle Behavior
```bash
# C-state residency
cpupower monitor 2>/dev/null | head -25
# C-state exit latencies
for state in /sys/devices/system/cpu/cpu0/cpuidle/state*/latency; do
  [ -f "$state" ] && echo "$(basename $(dirname $state)): $(cat $state) us"
done
# Which C-states are disabled
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
  for state_dir in "$cpu"/cpuidle/state*; do
    [ -f "$state_dir/disable" ] && [ "$(cat $state_dir/disable)" = "1" ] && echo "$(basename $cpu)/$(basename $state_dir): DISABLED ($(cat $state_dir/name 2>/dev/null))"
  done
done 2>/dev/null
# C-state limits
cat /sys/module/intel_idle/parameters/max_cstate 2>/dev/null || echo "intel_idle max_cstate sysfs not present (kernel 7.0+)"
# Energy performance preference
for cpu in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/energy_performance_preference; do
  [ -f "$cpu" ] && echo "$(dirname $(dirname $cpu)): $(cat $cpu 2>/dev/null)"
done 2>/dev/null | head -5
```

### LAYER 16: Proton/Wine/DXVK Gaming Config
```bash
# Check for NTSYNC
lsmod | grep ntsync
# Proton env vars
grep -rn 'PROTON_ENABLE\|DXVK_\|VKD3D_\|WINE\|STEAM' ~/.profile ~/.zshrc ~/.config/environment.d/ /etc/environment /etc/environment.d/ 2>/dev/null | grep -v '^\s*#'
# Steam launch options (if accessible)
cat ~/.local/share/Steam/userdata/*/config/localconfig.vdf 2>/dev/null | grep -i 'launch\|proton' | head -20
# MangoHud config
cat ~/.config/MangoHud/MangoHud.conf 2>/dev/null
# GOverlay config
cat ~/.config/gamescope/*.conf 2>/dev/null
# Gamemode config
cat /etc/gamemode.ini 2>/dev/null
cat ~/.config/gamemode.ini 2>/dev/null
```

## RESEARCH PHASE

After gathering ALL diagnostics above, you MUST search the web for EACH of these topics. Do NOT skip any:

1. **"[DISTRO] [KERNEL_VERSION] performance tweaks 2026"** — search for distro-specific kernel tuning
2. **"[CPU_MODEL] gaming latency tuning Linux"** — CPU-specific (e.g. "Arrow Lake 265K gaming latency")
3. **"[GPU_MODEL] Wayland KDE performance [DRIVER_VERSION]"** — GPU-specific NVIDIA Wayland tweaks
4. **"KDE Plasma [VERSION] compositor latency optimization 2026"** — compositor-specific
5. **"Linux kernel 7.x scheduler tuning gaming"** — kernel version-specific
6. **"Intel Arrow Lake hybrid CPU IRQ pinning Linux"** — architecture-specific
7. **"NVIDIA [DRIVER_VERSION] Wayland VRR issues fixes"** — driver-specific bugs
8. **"PipeWire low latency gaming config 2026"** — audio
9. **"Linux gaming [DISTRO] 2026 optimization guide"** — holistic gaming guides
10. **"systemd boot time optimization [DISTRO] 2026"** — boot speed

For each search, extract the TOP 3-5 actionable recommendations that are NOT already applied to this system.

## SYNTHESIS PHASE

Now combine your findings into ONE comprehensive output:

### Section A: CRITICAL FIXES (impact ≥ medium, effort ≤ medium)
Findings where the system is measurably suboptimal AND the fix is well-understood. Format each as:

```
### [N]. [TITLE] — Impact: [HIGH/MEDIUM]

**Current:** [actual value from diagnostics]
**Recommended:** [best practice value]
**Why:** [1-2 sentence explanation citing source]
**Commands:**
```bash
# Check current:
[diagnostic command]
# Apply fix:
[exact command(s)]
# Verify:
[verification command]
```
```

### Section B: CONFIG CONFLICTS
Any variable set to DIFFERENT values in different files, or any parameter that disagrees between config and runtime.

### Section C: STALE/UNUSED CONFIGURATIONS
Configs for hardware that doesn't exist (i915 on dGPU-only system, soundwire on HDA-only, thunderbolt, unused FS modules), services that shouldn't be running, coredumps wasting space.

### Section D: OPPORTUNITIES (impact ≥ medium, effort ≥ high)
Worthwhile improvements that require significant work (kernel recompile, BIOS changes, hardware upgrades). Present but don't pressure.

### Section E: VERIFICATION SUMMARY
A single copy-paste block of bash that the user can run at any time to verify all critical settings are still applied. This is the "health check" script.

## BANNED BEHAVIOR

- Do NOT apply any changes. Present commands only.
- Do NOT skip layers because "that's probably fine."
- Do NOT recommend without citing current state vs. recommended state.
- Do NOT use temporary/transient fixes. Every fix must be permanent (config files, systemd units, GRUB, sysctl.d, modprobe.d, etc.).
- Do NOT round-based reporting. Output everything at once.
- Do NOT apologize or use softening language. Facts and commands only.
- Do NOT make up values. If you can't determine the current state, say so and skip that item.
- Do NOT drop into explanations without showing the command first. Commands first, then brief explanation.
- NEVER enable or modify desktop HDR settings, display color profiles, or monitor OSD settings without explicit user request.
- NEVER install packages, change system configs, or take ANY system-modifying action. Audit only.

--- PROMPT END ---

## Usage

1. Open a new chat with any capable LLM (Claude, GPT-4, DeepSeek, etc.)
2. Paste the entire prompt block above
3. The LLM will run read-only diagnostic commands and produce a comprehensive audit
4. Review the output and run the recommended commands manually

## When to Re-Run

- After major kernel updates (e.g., 7.0 → 7.1)
- After NVIDIA driver updates
- After distro upgrades
- Every 3-6 months for general health
- When something "feels off" with performance
