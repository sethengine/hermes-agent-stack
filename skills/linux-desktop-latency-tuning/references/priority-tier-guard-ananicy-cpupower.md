# Priority-Tier Guard, ananicy-cpp, and cpupower.service

Captured 2026-08-07 on sethengine's Ultra 7 265K / Z890 / KDE Wayland workstation,
while chasing "apps and services have so high prio via nice in htop" and
"some apps boosted above kwin and plasma".

## The problem: ananicy-cpp misranks the desktop hierarchy
`ananicy-cpp` ("ANAother Auto NIce daemon", C++) is an auto-prioritizer that
watches processes every ~15s and rewrites `nice` from rules in
`/etc/ananicy.d/*.rules` + a type→nice map in `/etc/ananicy.d/00-types.types`.
On this box it bumped Hermes to nice -8 and could push games/electron launchers
above `plasmashell` (-6) and even near KWin. Anything above the compositor in
scheduling priority can starve the desktop → "USB input feels laggy" style
symptoms.

**Fix: disable it and replace with an explicit priority guard.**
```bash
sudo systemctl disable --now ananicy-cpp.service
```

## The real priority hierarchy on Linux (two dimensions)
| Dim | Meaning | Ordering |
|-----|---------|----------|
| **Scheduling class** | RT vs normal | FIFO > RR > TS (nice only matters WITHIN a class) |
| **nice** | TS-class priority | -20 (highest) … 19 (lowest) |

RT (FIFO/RR) ignores nice entirely — a FIFO task preempts ANY TS task. So the
correct way to keep USB/GPU IRQ threads above everything is the RT class, and
desktop apps that must stay preemptible use TS + negative nice.

### The `prio-guard` hierarchy (v2, validated)
```
SCHED_FIFO  prio 90   USB (xhci) + GPU (nvidia) IRQ threads   ← absolute top (kernel IRQ threads)
SCHED_RR    prio 41   kwin_wayland, keyd                      ← RT, above normal apps
SCHED_OTHER ni -12    pipewire, wireplumber                    ← high but PREEMPTIBLE
SCHED_OTHER ni  -6    plasmashell                              ← above normal apps
cap ni -10            stray apps (safety net, any user)        ← nothing else climbs higher
default                everything else
```

Key rules baked into the script:
- **pipewire must be TS + high nice, NOT RT.** A real-time (FIFO/RR) pipewire
  can monopolize a core and block everything else — the "pipewire bug". High-nice
  TS keeps audio above apps while staying preemptible. Do NOT use
  `chrt -f -p` for pipewire.
- **Safety cap**: demote any process (scan ALL users, not just the primary user)
  with nice < -10 back to -10, exempting the tier processes and kernel threads
  (`[kworker*]`, IRQ threads). Without the all-user scan, a root-launched stray
  slips through.
- IRQ threads are found by matching `irq/NNN-nvidia` / `irq/NNN-xhci_hcd`
  comm names; the actual IRQ numbers are discovered, not hardcoded
  (nvidia = 147-154, xhci = 131/139 on this box).
- Runs as a one-shot: at boot (via `fix-cpu0-hwp-boot.service`) and on resume
  (latency-fix hook step 3d). NOT a daemon — zero idle CPU.

### RT-class correctness (don't break this)
- `chrt -r -p 41 <pid>` sets RR41; `chrt -f` sets FIFO.
- Setting a process RT without cgroup/limits can pin a core; only IRQ threads
  and the tiny KWin/keyd processes belong in RT.
- `kernel.sched_rt_runtime_us=-1` (already in sysctl) is REQUIRED or RT tasks
  get throttled at 95% — which was the original random-lag cause.

## cpupower.service — making the no-op do something
`cpupower.service` is a systemd wrapper around `/usr/lib/cpupower/helper/cpupower.sh`
which reads `/etc/default/cpupower-service.conf`. Keys:
- `GOVERNOR='performance'` → `cpupower frequency-set -g performance`
- `PERF_BIAS` → `cpupower set-perf-bias`
- `EPP` → writes `energy_performance_preference`

**On HWP systems leave EPP out** — the EPP sysfs write returns `-EBUSY` (see
below) and would mark the service as failed. Just set `GOVERNOR`.

```bash
# /etc/default/cpupower-service.conf
GOVERNOR='performance'
```
`GOVERNOR=performance` is meaningful (verified: exit 0, all cores performance)
and fires at boot. This is the clean boot-time governor mechanism — prefer it
over tmpfiles.d or ad-hoc oneshots for the governor (see pitfalls).

## EPP on intel_pstate HWP: the -EBUSY story (corrects "silently ignored")
`/sys/devices/system/cpu/cpuN/cpufreq/energy_performance_preference` returns
**`-EBUSY` (Device or resource busy)** on write. This is NOT "ignored/clamped" —
in HWP mode intel_pstate owns EPP directly and refuses the sysfs write. Decode
the HWP MSR instead (no sudo read needed per-core is unreliable; cpu0 read
works):

```
IA32_HWP_REQUEST (MSR 0x774) byte layout:
  bits 7:0    min perf
  bits 15:8   max perf
  bits 23:16  desired
  bits 31:24  EPP         0x00=performance, 0x40=bal_perf, 0x80=bal_pow, 0xff=power
```
On this system the EPP byte was already `0x00` = **performance at the hardware
level** → no EPP tuning needed. Rule: **don't flag EPP, and don't write EPP on
HWP** — read the MSR byte, trust it, move on.

## Pitfalls (this subsystem)
- `sed /pattern/a\` inserts after EVERY matching line → triplicated blocks. Anchor
  on the FULL unique line; check `grep -c`; repair with `grep -v` + `sudo install -m 755`.
- tmpfiles.d (`/etc/tmpfiles.d/*.conf`) is a BAD place for cpufreq/EPP writes:
  the cpufreq nodes may not exist yet at tmpfiles time, and EPP returns -EBUSY
  → dead config that silently never applies. Use cpupower.service (governor) +
  the resume hook (per-wake fixes).
- Bare `wrmsr` in a systemd-sleep hook can silently no-op: hooks run with a
  minimal PATH. Always use the full path + load the module first:
  `modprobe msr; /usr/bin/wrmsr -p0 0x774 0x574757` (see
  `arrow-lake-hwp-bootcore-lock-resume.md`), and confirm the hook ran via its
  `logger` output in `journalctl`.
- `chrt -o -p 0` (SCHED_OTHER pid 0) is malformed and errors — pass the actual pid.
- Scanning only the primary user for the nice cap misses root-launched strays —
  scan all users.
