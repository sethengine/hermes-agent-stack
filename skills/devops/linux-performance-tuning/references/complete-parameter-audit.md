# Complete Parameter Audit — Subagent Delegation Prompt

Reusable template for offloading per-parameter sourced research to a subagent.
The main agent extracts the baseline (see SKILL.md workflow), then dispatches THIS
prompt so the subagent produces a full sourced `Recommendation | Current | Best | Source URL | Notes` table.

## Baseline files the subagent reads (created by main agent first)
- `~/audit/current_sysctl.txt`  — `sysctl -a` filtered to non-interface keys (`kernel.* vm.* fs.* net.core*/non-iface net.* user.* dev.* debug.* abi.*`)
- `~/audit/current_cmdline.txt` — `/proc/cmdline`
- `~/audit/current_cpu.txt`     — governor, driver, min/max_perf_pct, epp, max_cstate

## Subagent goal prompt (copy/paste)

> Produce a per-parameter tuning reference for a Linux desktop workstation. Baseline is extracted to files on disk — read them:
> - ~/audit/current_sysctl.txt  (each line is "key = value"; groups: kernel.*, vm.*, fs.*, net-core/non-interface net.*, user.*, dev.*, debug.*, abi.*)
> - ~/audit/current_cmdline.txt (kernel command line)
> - ~/audit/current_cpu.txt (governor, driver, min/max_perf_pct, epp, max_cstate)
>
> CONTEXT: Arrow Lake Ultra 7 265K (P-cores 0-7, E-cores 8-19), NVIDIA RTX 5060 Ti (driver 610.43.03), 64GB RAM, HP X34 3440x1440@165Hz, KDE Plasma 6 Wayland (compositing OFF, latency-low), Manjaro, kernel 7.1.4. Use case: low-latency desktop + gaming (Steam/Proton). Goal is MAXIMUM responsiveness/latency, NOT power saving or server throughput.
>
> YOUR TASK: For EACH parameter in those files, research the authoritative recommended value for THIS use case using web search / web_fetch of kernel.org docs (admin-guide/sysctl/vm.html, kernel-parameters.html), kernel-internals.org (sysctl-reference, sched-tuning), Red Hat docs, dolpa.me sched tuning, CachyOS/Arch tuning guides, NVIDIA forums, Proton docs. DO NOT give your own opinion — give the SOURCED best value.
>
> OUTPUT (write to ~/audit/recommendations.md): one markdown table per group (Kernel, VM, FS, Net, User, Dev, Cmdline, CPU) with columns: | Parameter | Current | Recommended | Source URL | Notes |
>
> RULES:
> - Only list parameters where a researched recommendation exists OR the current value should change. Group "leave at default" params under one note "(source: <url>)".
> - Prioritize latency-relevant: kernel.sched_*, vm.swappiness/dirty_*, vm.min_free_kbytes, vm.watermark_*, vm.overcommit_*, fs.* (file limits, inotify), net.core.*, net.ipv4.tcp_*, kernel.numa_balancing, kernel.timer_migration, kernel.sched_autogroup_enabled, kernel.ftrace_enabled, kernel.nmi_watchdog, kernel.panic, kernel.pid_max, kernel.perf_event_paranoid, kernel.yama.ptrace_scope, kernel.unprivileged_userns_clone, kernel.dmesg_restrict, kernel.kptr_restrict, kernel.printk, kernel.sysrq, abi.vsyscall32, dev.tty.legacy_tiocsti, debug.exception-trace.
> - Cmdline: research each token present AND recommend MISSING tokens a low-latency desktop should have (mitigations, iommu, nohz_full, etc.) with source.
> - EVERY Recommended value MUST have a real Source URL. No invented URLs. If you cannot find a source, write "no authoritative source found" — never guess.

## Why this structure works
- The subagent reads real current values from disk — no hand-copy drift.
- Enforces one sourced best value per parameter — the thing the user demanded.
- Groups the noise (~3000 per-interface net.* plus leave-at-default) so the ~60 meaningful rows stand out.
- Every row carries a source URL, turning "my takeaway" into "researched best option".