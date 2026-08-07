# Comprehensive Linux System Audit Prompt

Use this when asked to write an LLM prompt for a full system audit. The prompt tells the LLM to examine EVERY config, find conflicts, and produce prioritized fixes.

---

You are auditing a Linux system for performance and input lag. You have access to the full system config dump below.

Rules:
1. Investigate EVERY config file and parameter shown — not just the obvious ones.
2. Make reasonable assumptions about the hardware based on what the configs reveal.
3. Find conflicts, outdated workarounds, missing optimizations, and suboptimal defaults.
4. Prioritize fixes that reduce input lag and improve frame pacing.
5. Output only manual shell commands — never auto-execute.
6. For each finding: label it (CRITICAL/HIGH/MEDIUM/LOW), explain why it matters for this specific hardware, give the exact fix command, and say how to verify.

System configs to audit:
- `cat /proc/cmdline` — kernel boot parameters
- `cat /etc/modprobe.d/*.conf` — module options (nvidia, iwlwifi, etc.)
- `cat /sys/devices/system/cpu/cpu*/cpufreq/*` — per-core governor, EPP, frequency
- `cat /sys/devices/system/cpu/cpu*/cpuidle/state*/disable` — C-state configuration
- `cat /proc/interrupts` — IRQ distribution across all devices
- `nvidia-smi --query-gpu=gsp.mode.current,driver_version,pstate,clocks.*,power.draw,temperature.gpu --format=csv` — GPU state
- `systemctl list-units --failed` — failed services
- `journalctl -b -p err` — boot errors
- `cat ~/.config/powerdevilrc ~/.config/powermanagementprofilesrc` — power management
- `cat /usr/local/bin/pin-irqs-dynamic` — custom IRQ script if present
- `cat ~/.config/chrome-flags.conf` — Chrome/Chromium flags
- `lsmod | grep nvidia` — loaded NVIDIA modules
- `uname -r` — running kernel version
- `pacman -Qs nvidia` — installed NVIDIA packages (or equivalent package manager)
- `groups $USER` — user group membership
- `cat /proc/sys/vm/swappiness /proc/sys/vm/dirty_ratio /proc/sys/vm/vfs_cache_pressure` — VM tunables
- `sysctl kernel.timer_migration kernel.watchdog kernel.sched_autogroup_enabled` — scheduler sysctls
- `df -h /home` — disk fullness
- `ps -eo pid,pcpu,comm --sort=-pcpu | head -15` — top CPU consumers
- `cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io` — pressure stall info
- `cat /sys/kernel/sched_ext/state` — sched_ext active?
- `lscpu | grep -E 'Model|Core|Thread|NUMA'` — CPU topology
