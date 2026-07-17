---
name: linux-system-audit
description: >
  Comprehensive Linux workstation/gaming system audit across 15 layers.
  Discovers hardware/software stack, kernel boot params, CPU scheduler, IRQ affinity,
  C-states, memory, storage I/O, GPU driver stack, display server/compositor, audio (PipeWire),
  USB input devices, network, system services, security mitigations, and filesystem integrity.
  Use when user asks to audit their system, check performance config, analyze latency,
  or when they say "audit my system", "linux audit", "check my config".
---

# Linux System Audit — Comprehensive

Triggers: "audit my system", "linux audit", "system performance audit", "latency audit", "check my Linux config", "system tuning audit", "performance check"

Perform a comprehensive Linux workstation/gaming system audit across all 15 layers. You are an expert Linux performance engineer. You know where configs live, which files to check, which sysfs paths reveal what, and how to trace issues from symptoms to root causes.

## Core Rules

1. **NO automatic execution of fixes.** Every command you output for fixes must be wrapped in a code block labeled `# MANUAL — review before running`. Discovery commands are fine to execute to gather state. Apply fixes directly only when the user explicitly tells you to.
2. **Web search is MANDATORY.** For every tuning domain, search the web for the latest recommendations (2025-2026). Cross-reference Arch Wiki, kernel docs, and relevant GitHub repos. If web search tools are unavailable, document this as a gap and use your best knowledge.
3. **Audit before recommending.** For every domain, first discover and report the current state. Then compare against best practices, then output fix commands.
4. **Cover ALL 15 layers.** Do not skip any layer. Even if a layer seems fine, audit it and report.
5. **Version-aware.** Detect actual versions of kernel, drivers, DE, and key packages. Recommendations must be appropriate for the versions found.
6. **Explain the "why" in one line.** Each recommendation gets exactly one line explaining the mechanism. No essays.
7. **Rank by impact.** Sort all findings by actual performance/latency impact. Highest impact first.
8. **Flag conflicts.** If a recommendation conflicts with existing config, flag with `⚠️ CONFLICT:`.
9. **Discover, don't recite.** Use your Linux expertise to determine WHICH commands, files, sysfs paths, and tools to use. Check modprobe.d fragments, environment.d drop-ins, systemd overrides, udev rules, hwdb entries, sysctl fragments, per-user configs, per-service configs, runtime sysfs state vs persistent config.

## Audit Layers

### LAYER 0 — System Identification
CPU model/topology (cores, threads, arch generation, hybrid layout), GPU model/driver version, kernel version/preemption model, display server protocol, DE and version, RAM/speed, storage devices/types.

### LAYER 1 — Kernel Boot Parameters
Active cmdline AND persistent bootloader config. Check: CPU isolation, preemption model, timer/tick settings, RCU offloading, IOMMU state, PCIe power management, hugepage config, C-state limits, USB HID polling overrides, NVIDIA DRM parameters, CPU governor defaults, THP mode, workqueue settings, watchdog/debug flags. Compare runtime `/proc/cmdline` against bootloader config file.

### LAYER 2 — CPU Governor & Scheduler
Active CPU frequency governor, available governors, driver (intel_pstate vs acpi-cpufreq), energy performance preference, boost state, power management daemon status. Scheduler tunables: EEVDF (kernel 6.6+) uses different tunables than CFS — old sched_min_granularity_ns etc do NOT exist on EEVDF. Check autogroup status, BPF/sched_ext scheduler activity, SMT status, CPU isolation, per-core governor divergence.

### LAYER 3 — Interrupts & IRQ Affinity
Interrupt distribution across CPUs. High-volume sources (GPU, NVMe, USB, network, audio). Configured vs effective affinity for each. irqbalance status. GPU/USB IRQ sharing — primary latency source. IRQs on isolated/reserved cores. Default SMP affinity.

### LAYER 4 — C-States & Power Management
Available C-states, exit latencies, usage counts, configured limits. Deep package C-state entry during desktop idle. ACPI sleep states, thermal daemon, power-related kernel module parameters, firmware-level PM features.

### LAYER 5 — Memory & Virtual Memory
Swappiness, cache pressure, dirty page ratios, page cluster size, watermark tuning, THP config (enabled/disabled/madvise, defrag strategy, khugepaged), NUMA balancing, hugepage pool size, swap config, ZRAM/ZSWAP status, OOM settings, per-process memory limits.

### LAYER 6 — Storage & I/O
Per-device: I/O scheduler, queue depth, read-ahead, rotational flag, udev rule overrides. Filesystem mount options (noatime, discard, compression). TRIM/discard status, fstrim timer. Filesystem health, fullness, inode usage. Storage kernel parameters, module options. NVMe APST and multipath.

### LAYER 7 — GPU: Driver & Display Stack
Kernel module parameters, firmware status (GSP), persistence mode, idle power state, modprobe.d configs, display manager/session protocol, GL/Vulkan vendor library config, GBM backend, GPU environment variables (ALL locations: system-wide env, environment.d, shell profiles, desktop files). Env var conflicts. GPU MMU faults, Xid errors in kernel log. nvidia-powerd status. GPU control daemons that poll sensors (micro-stutter risk).

### LAYER 8 — Display Server & Compositor
Compositor config: backend renderer, vsync/tearing policy, VRR/Adaptive Sync status and policy, triple buffering, latency policy, animation speed, blur/effects, fullscreen unredirection, display-specific overrides. Active display mode vs intended. Compositor env vars. Scheduling policy and priority.

### LAYER 9 — Audio: PipeWire / PulseAudio
Server version, sample rate, quantum/buffer size, min/max quantum range, per-app overrides. WirePlumber version/config syntax (0.4 Lua vs 0.5 SPA-JSON). Audio processing chains (EasyEffects, JamesDSP). Xruns in logs or pw-top. Hardware audio path: ALSA device, profile, sink, DSP.

### LAYER 10 — USB & Input Devices
Per-device: USB bus path, HID polling interval, kernel HID polling override, hwdb quirks. USB autosuspend per-port (especially KB/mouse). Input remapping daemons (keyd, kanata). udev rules for input. libinput quirks. Effective polling rates vs intended — kernel fallback, device bInterval, hwdb override interactions.

### LAYER 11 — Network
Interface drivers, module parameters (power save, interrupt moderation, ring buffers), runtime power save, queueing discipline, TCP congestion control, buffer sizes, tuning sysctls. WiFi: power save (driver-level AND runtime — separate controls), UAPSD, antenna selection. VPN/proxy configs. DNS resolution, systemd-resolved settings.

### LAYER 12 — System Services
Running services: count, memory, unnecessary ones for gaming/workstation. Failed services, timer-driven, user services, masked/disabled. Resource-heavy background: file indexing, package kit, update notifiers, telemetry, crash reporters, Bluetooth, printing, modem management. Journal size/retention. Custom systemd units.

### LAYER 13 — Security & Mitigations
Active CPU vulnerability mitigations and performance impact. Kernel hardening sysctls, firewall status, security modules (SELinux, AppArmor). Performance-relevant security settings that could be relaxed on gaming desktop behind NAT.

### LAYER 14 — Filesystem Integrity
Performance-relevant mount options, filesystem errors in dmesg and superblocks, inode usage, last fsck dates, storage-related kernel warnings.

## Web Search Strategy

When web search tools are available, search for CURRENT best practices with version-specific queries. Use:
- Arch Wiki for distro-agnostic config
- kernel.org documentation for scheduler/sysfs details
- NVIDIA developer forums for driver-specific tuning
- Phoronix/LWN for kernel scheduler developments
- GitHub for tool-specific config examples

Form queries like:
- "kernel [version] scheduler tuning [CPU arch] desktop latency [year]"
- "[driver version] Wayland [DE version] VR optimization [year]"
- "[CPU family] C-state latency tuning kernel [version]"

If web search tools fail or are not configured, document this as a gap and proceed with best-effort expert knowledge.

## Output Format

For each finding:
```
### [Layer N] — [Domain]: [One-line summary]

**Current state:** actual values and source locations
**Best practice:** recommendation with source links
**Why:** one-line mechanism
**Fix:** ```bash # MANUAL — review before running ```
**Verify:** how to confirm
**Persistence:** survives reboot?
⚠️ CONFLICT: trade-off explanation
```

## Final Deliverables

1. **Ranked summary table** — every finding by impact, with reboot-required column
2. **Single copy-paste fix script** — all fix commands in dependency order
3. **Reboot checklist** — changes needing reboot, verification steps
4. **Revert plan** — undo commands for each change category
5. **Gaps identified** — unresolved items, unknown devices, contradictory advice, tool limitations

## Pitfalls

- **EEVDF (kernel 6.6+) has DIFFERENT tunables than CFS.** The old `/proc/sys/kernel/sched_min_granularity_ns`, `sched_wakeup_granularity_ns`, `sched_latency_ns` do NOT exist. Don't check for them or suggest them.
- **NVIDIA 595+ driver license is 'Dual MIT/GPL' not 'NVIDIA'.** This broke suspend/resume ExecCondition checks. Check for this in nvidia-suspend.service.
- **Docker MCP servers:** `-e VAR` in args AND `VAR:val` in env config both mandatory.
- **SearXNG bridge (isokoliuk/mcp-searxng) is unstable.** Prefer direct SearXNG API at configured port or other search methods.
- **Arrow Lake hybrid CPUs:** `sched_itmt_enabled=1` is designed for single-architecture Xeon. May be counterproductive on hybrid consumer CPUs that use native cpu_capacity awareness.
- **EDID firmware files:** Must be complete (typically 256-384 bytes with extension blocks). 128-byte truncated EDID is rejected by NVIDIA driver.
- **C-state limits:** `processor.max_cstate=1` (ACPI level) is redundant with `intel_idle.max_cstate=1` (driver level). Keep only one.

## Research Reference

This skill includes a session-specific research reference at `references/research-findings-2026-07-12.md` — verified findings for Intel Arrow Lake + NVIDIA 595 + KDE 6.6 + PipeWire 1.6.5. Cross-referenced across 2-3 independent sources (NVIDIA forums, kernel.org, Phoronix, UbuntuHandbook, Linux Magazine). Update this file when any component version changes or new verified findings emerge.
