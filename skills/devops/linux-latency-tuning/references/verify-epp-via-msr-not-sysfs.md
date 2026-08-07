# Verifying EPP/energy_preference — sysfs `default` is a false alarm under HWP

Source: live audit, Aug 2026, Arrow Lake Ultra 7 265K + RTX 5060 Ti, kernel 7.1, Manjaro.

## The trap

A performance audit flagging `energy_performance_preference=default` on every CPU as
"🔴 ONE real problem found" is WRONG on Arrow Lake with `intel_pstate=active` (HWP).
Investigating that false alarm ate most of the session.

- The kernel's `cpufreq` governor (`performance`) and the EPP hint are **two independent controls**.
- On HWP hardware the EPP is owned by firmware; the sysfs write returns `Device or resource busy`.
- The sysfs string `default` = "use HWP firmware default", NOT a mid-range EPP value.

## How to verify the true EPP (read the hardware MSR, not sysfs)

```bash
# 1. HWP active? IA32_PM_ENABLE MSR 0x770 bit 0 == 1 => HWP owns EPP
sudo rdmsr -f 0:0 -u 0x770

# 2. Real EPP: IA32_HWP_REQUEST MSR 0x774, bits 31:24
#    Read the FULL 64-bit msr, then mask the field (the -f 31:24 form can return
#    empty depending on rdmsr invocation; reading whole msr + masking is reliable)
VAL=$(sudo rdmsr -p0 0x774); echo "EPP=$(( (0x$VAL >> 24) & 0xFF ))"
#    0x00=performance  0x80=balanced_performance
#    0xC0=balanced_power  0xFF=power save
```

Live result: HWP on (MSR 0x770 = 1), EPP nibble = 0 (performance) while sysfs said `default`.

## Conclusion / correct action

- The `default` string is cosmetic under HWP. Leave it.
- Do NOT add EPP writes to the resume hook — the sysfs path is "busy" and the value is already optimal (dead code).
- The intel_pstate values that genuinely DON'T survive S3 are `min_perf_pct` and `hwp_dynamic_boost` — those are the ones the resume hook must restore.

## MSR decode note
- MSR 0x1B0 (IA32_ENERGY_PERF_BIAS) may be unreadable on this CPU — irrelevant when HWP EPP (0x774) is the active control.
- `rdmsr` can return empty for a bitfield read (`-f`); prefer reading the full register then shell-masking.