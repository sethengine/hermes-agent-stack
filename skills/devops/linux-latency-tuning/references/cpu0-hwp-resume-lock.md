# Arrow Lake cpu0 HWP resume-lock (boot P-core stuck at 400 MHz after suspend)

Source: live audit, Aug 2026, Ultra 7 265K (20c, 8P+12E) + Z890, kernel 7.1, Manjaro, KDE Wayland.

## Symptom
- One P-core (the boot core, **cpu0**) hard-stuck at **400 MHz** — *below its own 800 MHz floor* —
  while every other core boosts to 5.1-5.2 GHz and E-cores to 3.6-3.7 GHz.
- Governor already `performance`; no thermal throttle (all throttle counters 0); IRQs spread
  (not pinned to cpu0); `irqbalance` inactive; freq limits on cpu0's own policy are correct
  (800 MHz–5.4 GHz). None of this explains it.
- Appears **after a suspend/resume (S3/s2idle)** — boots normally, only froze low after the
  first resume. Keyed to the resume event, not a static BIOS setting.

## Root cause
On resume, the firmware/microcode clamps cpu0's **IA32_HWP_REQUEST MSR (0x774)** to a low
value. Decoded: `minimum=0xd`, `maximum=0xd`, `desired=0xd` = 13 → pins the boot P-core to
the slowest HWP state even though HWP "owns" frequency. The `cpufreq` governor is a
**separate control plane** from HWP pacing — so **`cpupower -g performance` cannot fix it**
(governor was already performance while cpu0 sat at 400-800 MHz for hours). Even forcing
`userspace` + `scaling_setspeed=3GHz` fails (400000), confirming the lock is in HWP MSR,
not the governor.

## Fix (verified working)
```bash
sudo wrmsr -p0 0x774 0x5757   # cpu0 immediately 800 MHz -> 5.2 GHz, holds under load
```
`0x5757` sets min=max=desired=0x57 (HWP state 0x57 = max turbo). Read current value first:
```bash
sudo rdmsr -p0 0x774           # 0xd0d (min&max&desired=0xd) => the lock
```

## Persistence — MUST be in the resume hook
Because this is a resume-only mark, put it in `/usr/lib/systemd/system-sleep/latency-fix`
under `case "$1" in post)` — right after the governor/min_perf_pct write:
```bash
wrmsr -p0 0x774 0x5757 2>/dev/null || true   # cpu0 HWP resume-lock fix
```
The existing latency-fix hook already re-binds the governor on resume; the MSR line is the
piece the governor-route can't cover. cpu0's idle drop back to ~800 MHz afterward is
**expected** (HWP parks idle cores); the test is that it reaches full turbo under load.

## Two deployment pitfalls (discovered Aug 2026)

1. **systemd-sleep hooks run with a MINIMAL PATH.** The hook calls the bare `wrmsr`.
   `wrmsr` lives in `/usr/bin` AND `/usr/sbin` (on Manjaro `/usr/sbin/wrmsr` is the real
   executable, `/usr/bin/wrmsr` a symlink). With a minimal PATH a bare `wrmsr` can fail
   silently, and the `|| true` swallows it — the hook "runs" but the MSR write never happens.
   `wrmsr` also needs the `msr` kernel module loaded. **Fix: use the absolute `wrmsr` path
   that exists plus an explicit `modprobe msr`**, logged (not `|| true`-stripped) so a
   lookup failure can't silently skip the fix. Pin the target explicitly with `-p 0` (boot
   core); don't rely on the default.

2. **Resume hook fires only on suspend→wake; cpu0 also relocks at power-on.** The Z890
   firmware re-locks the boot core at `0x774 = 0x0d0d` at **cold boot too**, not just after
   resume. A systemd-sleep-only fix therefore leaves cpu0 locked across a cold boot until the
   first resume. Pair the resume hook with a **boot-time service** running the same
   `modprobe msr && wrmsr -p0 0x774 0x5757` (oneshot unit, Before=online.target, or an
   rc.local / systemd-sleep alternative), so cpu0 is fixed before anything contends on it.

## Cheap diagnosis
```bash
# With a load on all cores, which core is below its architectural floor?
for i in $(seq 0 19); do printf 'cpu%-2s %4s MHz\n' "$i" "$(( $(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_cur_freq)/1000 ))"; \
  done | sort -k2 -n   # a P-core at 400-800 while siblings at 5100-5200 == candidate
sudo rdmsr -p0 0x774    # 0xd0d (min&max&desired=0xd) pattern = HWP clamp, not governor fault
```

## False lead warning (do NOT repeat)
This session I also raised EPP (`energy_performance_preference`) as a fix for intermittent
sluggishness and drafted a resume-hook EPP loop. That was wrong:
- The skill's own verified reference [`verify-epp-via-msr-not-sysfs.md`](verify-epp-via-msr-not-sysfs.md)
  shows EPP sysfs is `busy` under HWP-active and the MSR-measured EPP is **already 0x00
  (performance)** — a no-op write.
- The EPP writes were never applied (sudo blocked in the channel). Don't re-propose EPP edits
  to `latency-fix`; the real fix is the HWP-MSR line. When the user demands "just make it
  happen," answer with the verified CPU-lock finding, not an EPP dead-end. (For getting sudo
  into the latency hook automatically, reference `resume-hook-run-as-root-proxy.md`.)