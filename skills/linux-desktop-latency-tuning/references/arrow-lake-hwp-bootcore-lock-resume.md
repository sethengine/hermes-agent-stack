# Arrow Lake HWP Boot-Core Lock After Resume (Gigabyte Z890)

## The bug
Intel hybrid (P/E-core) systems — e.g. Ultra 7 265K on Gigabyte Z890 — can wake
from S3/suspend with the **boot processor (cpu0, a P-core) pinned at its HWP floor**
(~400–800 MHz) while every other core boosts to max (5.2 GHz). The whole desktop
feels abysmally laggy despite free CPU/RAM/thermals and a low load average,
because any single-thread work that lands on cpu0 runs ~13× slower.

**Key sign**: the core is stuck BELOW its own `scaling_max_freq` floor (800 MHz)
while `scaling_governor=performance`. A core stuck at 400 MHz when its cpuinfo
floor is 800 MHz is a strong signature — normal low-power idle parks at the
floor, never below it.

## Root cause (mechanism)
Firmware re-initializes per-core **HWP** (Hardware P-State) registers on resume
and writes cpu0's request register with both **max and desired = minimum ratio**:

```
IA32_HWP_REQUEST (MSR 0x774) read = 0x0d0d
  bits 7:0   min perf = 0x0d (13)
  bits 15:8  max perf = 0x0d (13)   <-- ceiling locked at the floor
  bits 23:16 desired    = 0x00 (autonomous)
```

## Why the `performance` governor CAN'T fix it
With `intel_pstate` in **active mode (HWP_ENABLED)** the CPU is autonomous; the
kernel "governor" is only a HINT written into the same HWP request register. If
the register's `max` field is checkpointed at the floor, there is nowhere for the
governor's hint to go — the register is the speed limiter.

| Attempt | Result |
|---------|--------|
| `cpupower frequency-set -g performance` | NO effect — governor already `performance`, register still capped |
| `echo performance > scaling_governor` (resume hook) | NO effect — re-writing the already-active gov no-ops the register-write; also can't override a capped max |
| `cpufreq scaling_setspeed=3000000` | NO effect — clamped to the capped max |
| `sudo wrmsr -p0 0x774 0x5757` | **Instant fix** — cpu0 800MHz → 5.2GHz, holds under load |

The `latency-fix` resume hook's "re-apply governor" step (echo performance) is
therefore INSUFFICIENT for this bug. The fix must write the MSR directly.

## The fix
```bash
sudo modprobe msr
sudo wrmsr -p0 0x774 0x5757   # writing HWP request only; max=desired=0x57, min=0x0d
```
Verify: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq` while loading
the core. (A broad per-core `rdmsr` loop sometimes returns blank — re-issue a
single-target `rdmsr -p0 0x774` read.)

## Persistence — use the RESUME HOOK, not a boot service
A boot-only systemd one-shot runs once at power-on but NOT on wake; the lock
returns on every S3 resume. Add the wrmsr to the EXISTING sleep hook so it fires
each `post` (alongside the governor re-apply):
```bash
# /lib/systemd/system-sleep/latency-fix  (or /usr/lib/..., NO .sh extension)
# after the "re-apply CPU governor" block (step 3):
modprobe msr 2>/dev/null || true
wrmsr -p0 0x774 0x5757 2>/dev/null || true
```

## Durable cure
The resume-time HWP re-init is a Gigabyte firmware defect. Recommend:
- BIOS → CPU Config: keep Intel Speed Shift, Turbo Boost, C-states ENABLED (a
  half-configured power state trips the resume path).
- A Gigabyte BIOS update fixes the HWP re-init on wake. Until then, the wrmsr in
  the sleep hook is the reliable mitigation.

## Confirmed innocent (don't chase these)
Thermal (BD PROCHOT=0, all throttling counters 0), the governor itself (already
performance), power daemons (upower doesn't set freq), irqbalance. It's a
firmware-level HWP lock, not OS/thermal.