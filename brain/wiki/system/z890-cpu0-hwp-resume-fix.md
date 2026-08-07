---
source: session 20260807 (System Sluggishness / Latency Tuning)
date: 2026-08-07
category: system/
---

# Gigabyte Z890 cpu0 HWP Lock on Resume — Fix

On a Gigabyte Z890 (BIOS F21) + Intel Ultra 7 265K (Arrow Lake), the **boot P-core (cpu0) gets hard-locked at 400–800 MHz after every suspend→resume**. This makes the entire desktop feel "abysmally slow" (low load average but terrible responsiveness) because cpu0 is the default target for early-boot interrupts and scheduler housekeeping.

## Root cause
The firmware re-initializes per-core HWP on wake and leaves **cpu0's `IA32_HWP_REQUEST` MSR (0x774) = `0x0d0d`** (min=max=desired=13 = floor). With `intel_pstate=active` (HWP), the CPU autonomously picks frequency from this register and **ignores the OS governor**. So `cpupower frequency-set -g performance` and `scaling_setspeed` **cannot** raise it.

## Why the obvious fixes fail
- **`performance` governor**: just a hint to HWP; the locked MSR wins → no effect.
- **sysfs `energy_performance_preference` write**: returns `-EBUSY` (intel_pstate owns EPP in HWP mode). Decoded HWP MSR shows EPP byte already `0x00` = performance at hardware level — no EPP action needed.

## The fix (MSR-level)
```bash
sudo modprobe msr
sudo /usr/bin/wrmsr -p0 0x774 0x574757   # min=max=desired=0x57, EPP=0x00
```
This immediately takes cpu0 from 800 MHz → 5.2 GHz. **Not persistent** — must be re-applied at boot and on every resume.

## Where it's wired (this host)
- `/etc/systemd/system/fix-cpu0-hwp-boot.service` (enabled): applies at boot, then runs `pin-irqs-dynamic` + `prio-guard`.
- `/lib/systemd/system-sleep/latency-fix` step 3b `fix_cpu0_hwp()`: writes `0x574757`, re-reads to confirm, retries once (firmware can re-lock cpu0 slightly after the hook fires), logs `hwp0_rc=`.
- Optional durable cure: Gigabyte Z890 BIOS update (F21 → newer) may fix the firmware HWP re-init at the source.

## Other cores
Only cpu0 is affected. Cores 8–13 had a forced-HWP-max pin that was **removed** by user request (kept IRQ pinning + C2/C3 off instead). All 20 cores boost correctly under load (P-core 5.2 GHz, E-core 3.6 GHz).

## Priority tier (separate issue, also fixed)
`ananicy-cpp` was misranking games/electron above plasmashell → disabled. Replaced by explicit `/usr/local/bin/prio-guard` v2: FIFO90 USB/GPU IRQs > RR41 kwin/keyd > TS ni-12 pipewire (NOT RT, safe) > ni-6 plasmashell > cap ni-10 strays.

See also: [[gigabyte-z890-aero-g-bios]], [[kwin-compose-values-landmine]], [[keyboard-latency-system-findings]]
