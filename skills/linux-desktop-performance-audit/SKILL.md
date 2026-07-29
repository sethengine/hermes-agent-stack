---
name: linux-desktop-performance-audit
description: "Systematic performance audit of Linux desktops — hardware, kernel, GPU (especially NVIDIA + Wayland), compositor, environment variables, storage, and VM tunables. Cross-references findings with current community research and produces prioritized recommendations."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [linux, performance, tuning, nvidia, wayland, gpu, kernel, audit]
    related_skills: [systematic-debugging, internet-research, last30days]
---

# Linux Desktop Performance Audit

## When to Use

Trigger when the user asks about:
- Improving desktop/game/GPU performance on Linux
- Stuttering, latency, or FPS drops on Wayland with NVIDIA
- Checking their system for missed optimization opportunities
- "What tweaks should I apply" or "audit my config"
- Comparing their setup against community best practices
- Diagnosing whether their kernel/GPU/env config is optimal
- Any combination of {Linux, Wayland, NVIDIA, performance, tweaks, tuning}

Also fire proactively when the user reveals their system stack (distro + GPU + display server) and the session context involves performance — many users don't know what they're missing.

## Core Principle

Do NOT guess at tweaks. Inspect first, then match findings to community data. The most valuable output is a prioritized list where each recommendation cites: (a) the measured current state, (b) what the recommended state should be, and (c) the effort/impact tradeoff.

## Round-Based Reporting Pattern

Do NOT dump every finding at once. Present in rounds:
- Round 1 = ~5-7 highest-impact findings. Let the user act on them.
- Round 2 = medium-impact polish items. Offer to go deeper.
- Round 3+ = edge cases, conflicts, tiny overhead items. Only when user asks for more.

Each round should cover a new layer (HW -> kernel -> GPU -> storage -> audio -> network -> desktop -> services) rather than re-iterating the same layer.

**User correction signal** — if the user responds with "all configs", "everything", "literally all", or any variant of frustration at the round-based approach, **immediately switch to comprehensive single-shot output**. Run the Full Config Enumeration batches (see `linux-latency-tuning` → "Full Config Enumeration for Comprehensive Audit") plus the File Audit layer below. The round-based approach helps most users, but this user has expressed a clear preference for "give me everything at once" and layering only increases frustration.

## Output Style Preference

When the user asks for a performance audit, default to commands-first, terse output. Show the exact command(s) before explanation. Avoid multi-paragraph analysis — let the numbers speak.

## The Layered Audit

Run ALL layers before synthesizing recommendations. Each is independent — fire in parallel batches.

### Layer 1: Hardware Inventory
```
cat /proc/cpuinfo | grep -m1 "model name"
cat /proc/cpuinfo | grep -c "^processor"
lspci | grep -i "vga\|3d\|nvidia"
free -h
lsblk -d -o NAME,SIZE,ROTA,MOUNTPOINT,MODEL
lscpu | grep -i numa
```

### Layer 2: Kernel + Boot Configuration
```
uname -a
cat /proc/cmdline
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort | uniq -c
cat /sys/kernel/mm/transparent_hugepage/enabled
```

### Layer 3: NVIDIA GPU + Driver
```
nvidia-smi --query-gpu=name,driver_version,power.limit,temperature.gpu,utilization.gpu,memory.total,memory.used --format=csv,noheader
lsmod | grep -i nvidia
cat /etc/modprobe.d/nvidia*.conf 2>/dev/null
ls /lib/firmware/nvidia/ 2>/dev/null | sort
```

### Layer 3b: Custom EDID Firmware (check for invalid overrides)
```bash
grep "drm.edid_firmware" /proc/cmdline
# If set, check the file:
ls -la /usr/lib/firmware/edid/*.bin 2>/dev/null
# Valid EDID must be >=128 bytes with header 00 FF FF FF FF FF FF 00
sudo dmesg | grep -i "Invalid firmware EDID"
```
If the kernel rejects the EDID file, the override is silently failing. See `references/nvidia-edid-firmware-diagnostic.md`.

### Layer 3c: NVIDIA fbdev (Wayland check)
```bash
cat /sys/module/nvidia_drm/parameters/fbdev
ls -la /dev/fb* 2>/dev/null
```
On Wayland-only, `fbdev=1` wastes VRAM on an unused console framebuffer. Fix: set `fbdev=0` in modprobe.d and rebuild initramfs.

### Layer 3c: LACTD GPU Daemon Polling
```bash
cat /etc/lact/config.yaml 2>/dev/null | grep -E 'interval_ms|apply_settings_timer'
```
Default `interval_ms: 500` polls the GPU every 500ms — can cause micro-stutters in games. Recommended: `interval_ms: 2000`, `apply_settings_timer: 30`.

### Layer 4: Wayland / Compositor
```
echo $XDG_SESSION_TYPE
grep -A20 '\[Compositing\]' ~/.config/kwinrc 2>/dev/null
cat ~/.config/environment.d/*.conf 2>/dev/null
```

### Layer 5: Environment Variables
Check ALL: /etc/environment, ~/.profile, ~/.config/environment.d/*.conf

Also scan for cross-file conflicts — the same var set to different values in different files:
```bash
grep -rn 'KWIN_DRM_OVERRIDE\|KWIN_DRM_ALLOW\|__GL_SYNC\|__GL_MaxFrames\|KWIN_DRM_DISABLE\|KWIN_TRIPLE\|GBM_BACKEND\|LIBVA_DRIVER' \
  /etc/environment ~/.config/environment.d/ /etc/environment.d/ 2>/dev/null | grep -v '^\s*#'
```

### Layer 5b: File Audit (comprehensive config dump)
When the user asks for "all configs" or the round-based approach isn't working, dump EVERY config file at once:

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
  ~/.zshrc
)
for f in "${config_files[@]}"; do
  [ -f "$f" ] && echo "=== $f ===" && cat "$f" && echo
done
```

### Layer 6: Storage + VM
```
mount | grep "^/dev/" | awk '{print $1, $3, $5, $6}'
cat /sys/block/nvme*/queue/scheduler
sysctl vm.swappiness vm.vfs_cache_pressure vm.dirty_ratio vm.dirty_background_ratio
cat /proc/meminfo | grep -Ei "HugePages_Total|HugePages_Free|Hugepagesize|Hugetlb"
```

### Layer 7: System Services
```
systemctl is-active irqbalance
systemctl is-active scx_loader
cat /sys/kernel/sched_ext/state 2>/dev/null
systemctl --failed --no-pager | head -20
systemd-analyze blame | head -5
```

### Layer 7b: WiFi Power Save (common hidden lag source)
```
iw dev 2>/dev/null | awk '/Interface/ {print $2}' | while read iface; do
  state=$(iw dev "$iface" get power_save 2>/dev/null)
  echo "$iface: $state"
done
```
`Power save: on` causes 10-100ms intermittent latency spikes as the NIC wakes from doze between packets. Fix: `sudo iw dev <iface> set power_save off` (immediate), and ensure `wifi-no-power-save.service` is running at boot.

### Layer 7c: Coredump Analysis (crashing services degrade perf)
```
sudo du -sh /var/lib/systemd/coredump/   # total waste
sudo ls -lh /var/lib/systemd/coredump/    | head -20  # per-crash breakdown
coredumpctl list 2>/dev/null             | head -20  # all crashes
```
Crashing services (EasyEffects, Steam, lactd, scx_rustland) spawn DrKonqi, write multi-MB coredumps to disk, and cause audio/gpu/scheduler glitches during restart. Clean: `sudo rm -rf /var/lib/systemd/coredump/*`. Disable collection entirely: `sudo systemctl mask systemd-coredump.socket`.

### Layer 7d: Process Count and Swap Pressure

High process count (700+) or swap usage despite free memory indicates resource pressure:

```bash
# Total process count + breakdown
echo "total: $(ps aux | wc -l) | user: $(ps --User=$(whoami) --no-headers | wc -l) | root: $(ps --User root --no-headers | wc -l)"
# Chrome/Electron renderer count (common bloat source)
echo "Chrome procs: $(ps aux | grep -c '[c]hrome')"
# Swap usage by process
for pid in $(find /proc -maxdepth 2 -type d -name '[0-9]*' 2>/dev/null | awk -F/ '{print $NF}'); do
  sw=$(grep -s "^Swap:" /proc/$pid/status 2>/dev/null | awk '{print $2}')
  if [ -n "$sw" ] && [ "$sw" -gt 0 ] 2>/dev/null; then
    echo "$sw kB - $(cat /proc/$pid/comm 2>/dev/null) ($(ps -p $pid -o args= 2>/dev/null | head -c80))"
  fi
done | sort -rn | head -10
# Swap detail
grep -E 'SwapCached|SwapTotal|SwapFree|Unevictable' /proc/meminfo
# Load and runnable
cat /proc/loadavg
grep procs_running /proc/stat
```

### Layer 7e: IRQ Distribution and Hot-Spots

Check whether interrupt load is concentrated on a single CPU (common NVIDIA issue):

```bash
# NVIDIA IRQ distribution
grep "nvidia" /proc/interrupts | head -6
# IRQ affinity vs effective_affinity mismatch
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  printf "IRQ %3d: mask=%s effective=%s\n" "$irq" \
    "$(cat /proc/irq/$irq/smp_affinity 2>/dev/null)" \
    "$(cat /proc/irq/$irq/effective_affinity 2>/dev/null)"
done
# Top IRQ spender CPU time
ps -eo pid,comm,time,%cpu,args --sort=-%cpu | grep -E 'irq|kwin' | head -5
# Context switches
grep "^ctxt" /proc/stat
# C-state residency by core
cpupower monitor 2>/dev/null | head -25

### Layer 8: Loaded Kernel Module Audit
```
cat /sys/class/drm/card*/device/vendor 2>/dev/null
lsmod | grep -E '\bi915\b'
lsmod | grep -E '\bsoundwire\b|\bsnd_sof\b'
lsmod | grep -E '\bthunderbolt\b'
lsmod | grep -E '\bjfs\b|\bhfsplus\b|\bhfs\b|\bufs\b|\bminix\b'
```

## Context Switch Analysis

```
grep "^ctxt" /proc/stat
CTXT1=$(grep "^ctxt" /proc/stat | awk '{print $2}'); sleep 3; CTXT2=$(grep "^ctxt" /proc/stat | awk '{print $2}'); echo "CS/s: $(((CTXT2 - CTXT1) / 3))"
```

### Interpreting Rates
- <10K/s: Idle
- 10-50K/s: Normal desktop
- 50-100K/s: Under load
- 100K+/s: Elevated

### RES IPI Storm Check
```
grep "RES" /proc/interrupts | awk '{for(i=2;i<=20;i++) print (i-2), $i}' | sort -k2 -rn
```

### Involuntary CS
Common cause on NVIDIA systems: GPU IRQs preempting the game thread. Check `grep nvidia /proc/interrupts` for concentration. Pin the game to P-cores that don't host GPU IRQs via gamemode.

## Hybrid CPU IRQ Pinning

Move ALL IRQs to E-cores. P-cores run the game with zero interruption.

```
# NVIDIA -> E-cores 8-9 (dedicated)
i=8; for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do echo "$((i % 2 + 8))" > /proc/irq/$irq/smp_affinity_list 2>/dev/null; ((i++)); done
# USB xHCI -> E-cores 10-11 (dedicated, never shared with GPU)
i=10; for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do echo "$((i % 2 + 10))" > /proc/irq/$irq/smp_affinity_list 2>/dev/null; ((i++)); done
```

**GPU and USB must NEVER share a CPU core.** GPU generates 100M+ interrupts. USB handles input. Each gets dedicated E-core pairs.

## Known Failure Patterns

### sched-ext / scx_loader (BPF schedulers)
Manjaro bundles scx_bpfland/scx_rustland, loaded by scx_loader.service. The daemon uses ~100-180 MB peak memory and adds a scheduling layer over the kernel's built-in EEVDF. On P-core + E-core systems, this can increase context-switch overhead.
- Diagnose: systemctl is-active scx_loader and cat /sys/kernel/sched_ext/state
- Fix: sudo systemctl stop scx_loader.service (immediate revert to kernel scheduler); sudo systemctl disable scx_loader.service (permanent)

### Kernel modules for absent hardware
- i915 on dGPU-only systems (5 MB + cascade of drm_display_helper/ttm/drm_buddy/intel_gtt)
- soundwire_intel/snd_sof* on HDA-only audio
- thunderbolt on desktop with no TB devices
- jfs/hfsplus/ufs/minix for unused filesystems
- Fix: Add blacklist lines in /etc/modprobe.d/*.conf, rebuild initramfs

### PipeWire audio
See references/pipewire-audio-diagnostics.md for patterns:
1. Unquoted SPA-JSON strings causing "Expected object key" (e.g. `resample.method = soxr` — unquoted string parsed as key)
2. WirePlumber auto-sink vs manual sink front:1 contention
3. DMAR INTR-REMAP faults from NVIDIA HDA audio (fix: snd_hda_intel.enable=0,1)
4. EasyEffects crashes from corrupted INI-as-JSON presets (file starts with `[General]` → `[G` parse error → SIGABRT)
See references/easyeffects-crash-chain-investigation.md for the full crash cascade, diagnostic signals, and repair sequence.
### Intel IOMMU DMAR faults
NVIDIA HDA audio (PCI 02:00.1) generates constant INTR-REMAP faults with intel_iommu=on. Fix: snd_hda_intel.enable=0,1 in modprobe.d

## Common Pitfalls
- Don't flag SMT=0 on Arrow Lake (no HT on P-cores)
- intel_pstate "powersave" != ACPI "powersave" — check energy_performance_preference
- DXVK_ASYNC was removed in DXVK 2.0
- irqbalance conflicts with custom pin-irqs-dynamic.service
- Check all env var sources (systemd, shell, profile)
- USB autosuspend adds 3-10ms intermittent input latency
- GPU + USB IRQs on same core causes input latency spikes
- Game involuntary CS is usually from GPU IRQs, not the scheduler
- Proton/Wine has inherently high voluntary CS — don't flag it
- **Kernel 7.0+ removes CFS tunables** — `sched_min_granularity_ns`, `sched_wakeup_granularity_ns`, `sched_latency_ns` don't exist. EEVDF is the sole scheduler. See `linux-performance-tuning` references/eevdf-kernel-7.0-transition.md
- **`sched_itmt_enabled=1` on Arrow Lake hybrid** — ITMT is for single-architecture Xeon, not hybrid consumer CPUs. The kernel's native cpu_capacity already handles P-core priority. Having both active can double-prioritize P-cores and starve E-cores. Remove from GRUB on Arrow Lake/Raptor Lake systems.
- **Custom EDID firmware rejected by NVIDIA** — 128-byte files are incomplete. Valid EDID is 256 bytes (EDID 1.3+). Check with `sudo dmesg | grep "Invalid firmware EDID"`. Fix or remove the `drm.edid_firmware=` parameter.
- **ModemManager running on desktop with no cellular modem** — 8+ MB wasted. `sudo systemctl disable --now ModemManager`

## References
- references/pipewire-audio-diagnostics.md — PipeWire + DMAR fix patterns
- references/gigabyte-z890-bios-stability.md — BIOS settings
- references/chrome-nvidia-wayland-screen-blanking.md — KDE 6 + Chrome wake failures
- references/sethengine-system-audit-june-2026.md — Full system audit
- references/hardware-voltage-sensor-investigation.md — Missing sensors
- references/sata-hotplug-no-reboot.md — SATA diagnostic
- references/nvidia-edid-firmware-diagnostic.md — Custom EDID validation failures
