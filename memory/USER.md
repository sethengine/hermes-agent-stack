ALC1220 alc1220-sink(hw:1,soxr-vhq). XM3+Douk. EE active: BassEnh→EQ#0→EQ#2(highcut)→EQ#3(warm). Rest bypassed.
§
Z890 + Ultra 7 265K + RTX 5060 Ti (610) + KDE Wayland + 165Hz. kernel 7.1. GRUB quirks+cstate+sync perf. KWin OFF. PPD off. keyd ACTIVE (grave→esc mapping) — keep. Resume: post.
§
Doom Emacs, classic Emacs keys (no evil). C++ dev, wants VS Code-like intellisense. Give direct commands, not theory.
§
Steam/Proton: Manjaro+RTX5060Ti+Z890+KDE 165Hz. GE-Proton11-1, MangoHud, D2R (2536520). DLAA>DLSS. Cron DLSS auto-update via loathingkernel. Custom DXVK-NVAPI from source for DLAA DRS.
§
English only — no translations or non-English responses. All communication must be in English regardless of what language the user writes in.
§
Must ask before restarting KWin or any disruptive action. Question assumptions — don't blindly apply fixes without critical thought.
§
Investigate first before modifying. NEVER change config files (pipewire, etc.) or restart services without permission. 'Only investigate' = read-only.
§
Commands-first, no theory, minimal commentary. Investigate ALL configs/processes comprehensively, not selectively. Frustrated by stale file compares, going off-track, incomplete work. Verify file versions before presenting. Runs Docker with self-hosted services (RabbitMQ). Developer/power user with complex multi-service system.
§
Ultra 7 265K (Arrow Lake, intel_pstate=active, HWP): EPP "default"=fine (HWP owns MSR 0x774 bits31:24=0); sysfs EPP write fails, don't flag. Z890 RESUME bug: firmware re-locks BOOT CORE cpu0 at min HWP (0x774=0x0d0d) after suspend/wake; `performance` governor CANNOT fix a register-locked HWP — fix `wrmsr -p0 0x774 0x574757`, hook into /lib/systemd/system-sleep/latency-fix step 3b for every wake. rdmsr on non-boot cores returns blank (read artifact) — trust scaling_cur_freq, not the MSR read.
§
Latency-tuning stack (2026-08-07, applied): cpu0 HWP fix via /etc/systemd/system/fix-cpu0-hwp-boot.service (enabled, boot) + /lib/systemd/system-sleep/latency-fix step 3b fix_cpu0_hwp() (resume, verify+retry). IRQ pin /usr/local/bin/pin-irqs-dynamic v6b: GPU(147-154)->cpu8-11, USB xhci(131,139)->cpu12-13, C2/C3 off 8-13, NO forced-max MSR on 8-13 (user removed). Priority guard /usr/local/bin/prio-guard v2: FIFO90 USB/GPU IRQs > RR41 kwin/keyd > TS ni-12 pipewire(not RT, safe) > ni-6 plasmashell > cap ni-10 strays. ananicy-cpp DISABLED (misranked games above plasmashell). cpupower.service configured GOVERNOR=performance. Loose end: ~/99-performance.conf.clean (dead tcp_low_latency) NOT yet installed.
§
For system audits ('go through every param & find best'), wants (1) FULL parameter surface (all meaningful sysctl ~340, cmdline, env), NOT just already-tuned layers — partial coverage is rejected as 'crap'; (2) researched, sourced best value (real URL) per row, NOT my ✅/⚠️ opinion verdict; (3) plan first before acting. Frustration with incomplete/opinionated audits is a recurring theme, announced explicitly.