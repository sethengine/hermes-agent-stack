---
name: linux-parameter-audit
description: Audit all Linux tunables with sourced best values.
---

# Linux Parameter Audit — Comprehensive & Sourced

This skill performs a beginning-to-end audit of every parameter a Linux system
exposes. The defining rule is that every row cites a real source and every
"leave-default" row states the documented default and why it is appropriate.
We do NOT invent values or summarize categories.

## When to use
- "audit every parameter / config on this system"
- "go through all system params and find the best one"
- "is anything disabling or handicapping performance?"
- A pre-tuning pass before applying changes.

## The methodology (proven, context-efficient)

The naive approach (one web search per parameter times 3500) fails because
search is rate-limited and thousands of searches is absurd. The correct approach
uses the authoritative kernel documentation as the per-key source of truth.

1. Extract the EXACT key list from the live system, not categories.
   - sysctl groups: `sysctl -a 2>/dev/null | grep -E "^<group>\." | sort`
   - cmdline: `cat /proc/cmdline | tr ' ' '\n'`
   - sysfs: `find /sys/... -type f -writable`, `ls /sys/block/*/queue/`
   - configs: read the actual files (modprobe.d, kwinrc, gamemode.ini, udev, env).

2. Fetch the authoritative doc ONCE per group, not per key. Primary sources,
   in priority order:
   - sysctl kernel/vm/fs/user/dev/debug/abi:
     https://www.kernel.org/doc/html/latest/admin-guide/sysctl/<group>.html
   - net: https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html
   - cmdline: https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html
   - cpu freq: .../admin-guide/pm/intel_pstate.html, pm/cpufreq.html, pm/cpuidle.html
   - block/io: .../block/index.html, .../admin-guide/cgroup-v2.html
   - NVIDIA: https://wiki.archlinux.org/title/NVIDIA
   - KWin: https://community.kde.org/KWin , https://invent.kde.org/plasma/kwin
   - gamemode: https://github.com/FeralInteractive/gamemode
   - Proton: https://github.com/ValveSoftware/Proton/wiki
   - Arch Wiki for desktop-specific surfaces.

   Use web_extract with a generous char_limit (about 60000). The doc is saved to
   a local .md path in the result; READ THAT FILE to get per-key defaults. The
   doc text names each key and its default/intent; that is the "best option"
   basis for non-latency-critical keys.

3. For each key, build the row:
   - Current = actual value from step 1.
   - Best Option = documented default if current matches or is fine; otherwise
     the latency-appropriate value with the reason. For keys with NO tuning
     relevance (read-only/identity such as version, hostname, tainted,
     ns_last_pid, random.uuid, pty.nr, *_next_id), mark not-tunable and cite the
     doc section that shows it is runtime/readonly.
   - Source = the exact doc URL (per-group is acceptable; deep-link the anchor
     when the extract shows one).
   - Apply? = yes / no / leave-default / not-tunable.

4. Latency-specific overrides (for a low-latency desktop/gaming use case;
   confirm use case with the user first). Where the kernel default is
   power/throughput-biased, recommend the latency-biased value and cite BOTH the
   doc default AND a latency guide (kernel-internals.org/sched/sched-tuning/,
   CachyOS optimization guide, Phoronix). Examples: vm.swappiness 60 to 5-10,
   intel_idle.max_cstate=1, preempt=full, sched_autogroup_enabled=0, THP
   enabled/defrag always to madvise (kernel.org/mm/transhuge.html).

## Output format
Write a markdown doc (for example ~/audit/recommendations.md) with one section
per surface and a table per group:
  | Parameter | Current | Best Option | Source URL | Apply? |
End with a "Recommended Changes" section listing ONLY Apply?=yes rows, grouped,
with the exact file and change. Do NOT apply anything without explicit user
approval.

## Scope handling (important; user may want ALL or RELEVANT)
- If the user says "every param / even a million": iterate ALL groups, including
  the 3300 per-interface net.<iface>.* (summarize by interface type, but list
  global net.core.* / net.ipv4.* individually).
- If the user scopes to "what can handicap performance": restrict exhaustive
  per-key research to scheduler/VM/CPU-freq/IO/net-core/cgroup/THP/configs, and
  explicitly mark peripheral sysctls as out-of-scope rather than fake rows.

## Pitfalls
- sudo does NOT work from the agent terminal (password prompt fails). For
  root-only reads (debugfs /sys/kernel/debug/sched/features,
  /proc/driver/nvidia/params), note "needs root"; do not fabricate values.
- sysfs /sys/kernel/debug/* and notes files may be binary; read with care.
- Subagents for this task hit HTTP 503 capacity errors; prefer doing the work
  inline with web_extract (which is reliable) over dispatching delegates.
- web_search is frequently rate-limited/empty; rely on web_extract of known doc
  URLs instead of searching.
- Verify each current value from the live system; never assume.

## OPERATIONAL GOTCHAS (learned the hard way — read before running)
1. **netcore.list per-interface trap.** `sysctl -a` dumps ~3300 per-interface
   keys (net.ipv4.conf.<iface>.*, net.ipv6.conf.<iface>.*). A naive
   `grep -vE "^net\.[a-z0-9]+\.[a-z]"` DELETES the global `net.core.*` /
   `net.ipv4.*` keys too (they match the same shape). Extract globals
   EXPLICITLY:
     grep -E "^net\.core\." file
     grep -E "^net\.ipv4\." file | grep -vE "^net\.ipv4\.conf\.[a-z0-9]"
     grep -E "^net\.ipv6\." file | grep -vE "^net\.ipv6\.conf\.[a-z0-9]"
   Then summarize per-interface conf keys by interface type (lo / eth / wlp /
   veth / docker / br) — do NOT emit 2478 individual rows.
2. **FALSE-OVERRIDE rule (critical).** Before marking any row Apply?=YES,
   GREP THE LIVE VALUE and compare. The draft will confidently assert
   "current=default, recommend=X" when current is ALREADY X. Example hit:
   tcp_ecn was already 2 (optimal) and tcp_tw_reuse already 1 — both were
   wrongly flagged as changes. Always read the live value; if it already
   matches the recommendation, mark leave-default, NOT yes.
3. **Context management — generate tables with a script, not inline.** Emitting
   950 net rows inline will blow the context budget. Write a small python
   script (or use execute_code) that loads the key list + doc defaults and
   writes the .md. Keep the doc text in a separate cached file; do not paste
   huge extracts into the conversation.
4. **Command-parser blocklist.** Long inline command lines (heredocs, big
   for-loops, multi-grep pipelines) get BLOCKED as "unparseable payload".
   Write them to a .sh file and run `bash file.sh` instead. Same for complex
   grep chains.
5. **grub cmdline is additive.** When adding tokens (transparent_hugepage=
   madvise, nvidia_drm.fbdev=0), APPEND to the existing GRUB_CMDLINE_LINUX,
   never replace — the real cmdline lives in /proc/cmdline, not the grub
   template file. Strip any pre-existing copy of the token first to avoid
   duplicates, then append.
6. **Config-file invalid-key detection.** Audit config files KEY-BY-KEY
   against the project's documented schema, not just "does it parse". Found:
   gamemode.ini had `intel_pstate = no_hwp` (not a valid gamemode [gpu] key)
   and a dead `scxctl switch -s bpfland` line (sched-ext not mounted). Remove
   invalid/dead keys; keep the file minimal and valid.

## Resume & State (plan + log — NEVER miss a thing)

This task is long and can be interrupted (context limits, capacity errors,
user mid-conversation). To guarantee nothing is skipped and a run can RESUME
**from disk, not from conversation memory**, maintain state files in the audit
working dir AND use the bundled helper scripts in `references/`.

### Bundled helper scripts (in references/)
- `references/extract_keys.sh` — extracts the EXACT key list from the live
  system into `./batches/` and `./baseline/` (so a resume never re-derives).
- `references/resume_check.sh` — reads ONLY disk state (AUDIT_PLAN.md +
  batch files) and reports what is DONE vs MISSING. Run this FIRST on resume.
- `references/AUDIT_PLAN.template.md` — copy to `AUDIT_PLAN.md`, fill Keys
  from the extract counts.
- `references/doc_urls.txt` — the exact authoritative URLs to web_extract
  per group (fetch once per group, read the cached .md for per-key defaults).

### AUDIT_PLAN.md — the exhaustive checklist
One row per batch/group, with a status column. Created ONCE at start from the
exact key extraction (step 1). Example shape:

    # Audit Plan
    | Batch | Group / Surface            | Keys | Status   | Output file            |
    |-------|----------------------------|------|----------|-----------------------|
    | A     | sysctl kernel.*            | 142  | DONE     | batchA_kernel.md      |
    | B     | sysctl vm.*                | 50   | DONE     | batchB_vm.md          |
    ...

Status values: PENDING | IN_PROGRESS | DONE | SKIPPED (with reason).
The full key COUNT must be derived from the live extraction, not estimated.

### AUDIT_LOG.md — append-only run log
Every action appended as it happens, with timestamp + result. Example:

    2026-08-07 19:40  [A] kernel.* extracted (142 keys) + kernel.html fetched -> batchA_kernel.md DONE

### Resume rule (MANDATORY at skill start)
1. Run `bash references/resume_check.sh`. It reports DONE vs MISSING from disk
   ONLY — no reliance on conversation context.
2. If AUDIT_PLAN.md + batch files exist: skip DONE batches; resume at the first
   PENDING/IN_PROGRESS. Re-run only what is missing.
3. If nothing exists: run `bash references/extract_keys.sh`, then copy
   `references/AUDIT_PLAN.template.md` to `AUDIT_PLAN.md` and fill the Keys
   counts from `wc -l batches/*.list`. Write the plan BEFORE any research.
4. Before each batch: Status=IN_PROGRESS + log line. After: DONE + log line.
5. After the LAST batch: COMPILE master from all batch files (consolidated
   "Recommended Changes" from every Apply?=yes row). Do NOT write master until
   all batches DONE.

This disk-state discipline is what makes the audit resumable and complete even
if the conversation is compressed or lost.

## Verification
- After writing each batch file, grep that every Apply?=yes row has a real
  http(s) source and a concrete current value. Spot-check 3 random rows
  against live sysctl/files to confirm accuracy.
- At the end, confirm AUDIT_PLAN.md shows every batch DONE (or SKIPPED with
  reason) before declaring the audit complete.

## Generating fix files (after audit approved)
Once the user approves the Recommended Changes, produce APPLY-READY artifacts
in a `fixes/` subdir (NOT applied — user runs with sudo, agent has no sudo):
- `fixes/<file>.clean` — cleaned version of each config to replace (gamemode.ini,
  /etc/environment, etc.). Keep only valid keys; remove invalid/dead ones.
- `fixes/grub_cmdline.txt` — the new full GRUB_CMDLINE_LINUX with appended
  tokens (additive; strip pre-existing copies first).
- `fixes/apply_fixes.sh` — a script the USER runs via `sudo bash
  apply_fixes.sh`. It `install`s the .clean files, sed-appends GRUB tokens,
  re-runs any boot script (pin-irqs), and prints post-reboot verify commands.
  The script must be idempotent (skip if already applied).
- Provide the explicit manual commands too, in case the user prefers copying
  them. Never run sudo from the agent; hand the commands to the user.
