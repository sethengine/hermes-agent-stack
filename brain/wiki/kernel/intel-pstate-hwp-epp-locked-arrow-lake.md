---
source_session: "20260707_181617_f5bd6e"
date: 2026-07-07
category: kernel
tags: [intel_pstate, hwp, epp, arrow-lake, kernel-7.0, locked, energy_performance_preference]
related: [intel-pstate-epp-default, cpu-min-perf-pct-systemd-permanent]
---

# Intel P-State HWP EPP Locked on Arrow Lake + Kernel 7.0

On Arrow Lake (Intel Core Ultra 7 265K) with kernel 7.0 and `intel_pstate=active`, the `energy_performance_preference` sysfs is **locked by HWP firmware** — writes fail silently, even as root.

## The Behavior

```bash
# This fails silently
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference

# cpupower also fails
cpupower set --energy-perf performance
```

HWP (Hardware P-State) mode means the on-die controller owns frequency decisions. The firmware locks EPP to prevent OS override.

## Workaround Options

| Option | Effect | Trade-off |
|--------|--------|-----------|
| `intel_pstate=passive` | Unlocks EPP, enables `cpupower` control | **Loses HWP dynamic boost** — worse burst performance |
| `min_perf_pct` tuning | Raises CPU floor frequency | Coarse-grained, no per-core |
| Accept default EPP (0x80) | No change needed | `balance_performance` is already sensible |

## Verified on Arrow Lake (kernel 7.1/610) via MSR

The sysfs `energy_performance_preference` shows `default`, but archiving the hardware register directly revealed the true state (2026-08-07, session re-verification):

```bash
# IA32_HWP_REQUEST (MSR 0x774) — EPP field is bits 31:24
rdmsr -p 0 0x774      # → 0x57xx; EPP nibble already 0 = "performance"
wrmsr 0x774 0x00000000  # writes EPP=0 successfully (exit 0)
```

**Key finding:** On this Arrow Lake system HWP is enabled and the MSR EPP field is already `0` (max performance) in hardware — the sysfs `default` label is misleading and is **NOT a handicap**. Do not flag or try to change it. `wrmsr 0x774 0x0` succeeds, confirming the hardware value is correct as-is.

## Recommendation

Keep `intel_pstate=active` for HWP dynamic boost benefits. Use `min_perf_pct=70` via systemd unit instead of trying to set EPP. HWP with the default EPP hint already gives good desktop performance.

## Z890 Resume Lock — cpu0 Stuck at Min HWP (0x0d0d) — 2026-08-07

Separate from the EPP-lock: on suspende→resume the **Gigabyte Z890 firmware re-initializes per-core HWP and leaves the boot core (`cpu0`) pinned at its minimum** (`IA32_HWP_REQUEST` MSR `0x0d0d`), while all other cores boost to 5.2 GHz. The `performance` governor your resume script sets **cannot** fix a register-locked HWP. Confirmed **not thermal** (BD PROCHOT=0, ALL thermal counters 0). Same session: good-good all-cores stress showed cpu0 stuck at 400 MHz (below its 800 MHz floor) while others boost to 5.1–5.2 GHz.

**Fix — add to resume hook `/lib/systemd/system-sleep/latency-fix` step 3b:**

```bash
# 3b. Fix cpu0 HWP request stuck at min after resume (Z890 firmware bug)
modprobe msr 2>/dev/null || true
wrmsr -p0 0x774 0x5757 2>/dev/null || true   # write boot core back to performance
```

**Two critical pitfalls discovered while deploying this:**
1. **systemd-sleep hooks run with a minimal PATH** — and the hook calls bare `wrmsr`. `wrmsr` (at `/usr/bin/wrmsr` and `/usr/sbin/wrmsr`) requires the `msr` module loaded; the `|| true` swallows any "command not found"/failure silently. The fix needs the **full path** to `wrmsr` plus `modprobe msr` so a lookup failure can't silently skip the fix. On Manjaro `/usr/sbin/wrmsr` may be the real executable while `/usr/bin/wrmsr` is a symlink — use the absolute path that exists.
- **Boot-time gap:** the hook only fires on suspend→wake, but cpu0 relocks at `0x0d0` at **power-on too** (not just resume). A pure systemd-sleep hook leaves cpu0 locked across a cold boot. Pair the resume hook with a **boot-time service** (systemd unit or `rc.local` equivalent) that runs the same `modprobe msr` + `wrmsr -p0 0x774 0x5757` at startup so cpu0 is fixed before anything contends for it.

**MSR byte layout (0x774, IA-32_HWP_REQUEST):** byte0=min, byte1=max, byte2=desired, byte3=EPP. cpu0=`0x00000d0d` → EPP already 0 (performance) but min/max/desired pinned low; writing `0x5757` lifts it.

## References
- [[intel-pstate-epp-default]]
- [[cpu-min-perf-pct-systemd-permanent]]
- [[linux-tuning-config-audit-dead-entries]]
