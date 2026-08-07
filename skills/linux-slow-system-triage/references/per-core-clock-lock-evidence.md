# Per-core clock lock — concrete evidence pattern (Aug 2026, Gigabyte Z890 + Ultra 7 265K)

Session detail backing SKILL.md Rule 4. The user reported "all apps + OS abysmally slow" after
Rules 1-2 (near-full /home, broken AppImage FUSE mounts, always-on Docker) were already cleared.

## The decisive probe output

Per-core dump (all 20 threads, Arrow Lake 265K: P-cores 0-7, E-cores 8-19):

```
cpu0: 400 MHz      <- boot BSP, stuck
cpu1: 4601 MHz     <- P-core sibling at boost
...
cpu12: 799 MHz     <- idle E-core at floor (normal)
cpu17: 5203 MHz    <- boosted
```

cpu0's own limits were NOT clamped (so it was not a sysfs max_freq issue):

```
cpu0: scaling_min_freq=800000  scaling_max_freq=5400000  governor=performance  affected_cpus=0
cpuinfo_min_freq=800000  cpuinfo_max_freq=5400000
```

Yet it read 400 MHz — BELOW its own 800 MHz floor → hardware/firmware clamp, not a policy choice.

## Decisive OS-cannot-override test

```bash
echo userspace | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor >/dev/null
echo 3000000  | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed >/dev/null
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq   # STILL 400000 — firmware lock proven
echo performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor >/dev/null
```

Also confirmed under synthetic pinned load (`timeout 2 taskset -c 0 bash -c 'while :; do :; done'`)
cpu0 stayed 399988-400018 kHz → not a misread, not an idle artifact.

## Differential checks that RULED OUT Linux-side causes

| Check | Command | Result |
|---|---|---|
| Thermal throttle | `cat /sys/devices/system/cpu/cpu0/thermal_throttle/*_count` | all 0 (also cpu1) |
| Power daemons | `systemctl is-active power-profiles-daemon thermald tuned` | all inactive; upower does NOT set CPU freq |
| IRQ affinity | loop `/proc/irq/*/smp_affinity`; `systemctl is-active irqbalance` | affinity spread (fffff/fc000), zero IRQs pinned to cpu0 alone; irqbalance inactive but irrelevant |
| GPU | `nvidia-smi -q -d PERFORMANCE,CLOCK` | P0, 2107 MHz graphics, persistence on |
| Fontconfig | `fc-cache -f`, `du -sh ~/.cache/fontconfig` | 19M valid cache, 5580 fonts |
| Chrome proxy | `/proc/<pid>/environ`, Preferences | none |
| CPU temp | `sensors` | ~43°C |

## Red herring captured (do not repeat)

DBus calls against KWin compositor:

```
QDBusConnection: couldn't handle call to suspend, no slot matched
Could not find slot CompositingAdaptor::suspend / ::resume
```

These lines appear in the KWin journal AFTER *you* call
`dbus-send --dest=org.kde.KWin /Compositor org.kde.kwin.Compositing.suspend` — the method name
differs on this KWin build, so the call fails and KWin logs it. They are artifacts of your own
probe, NOT evidence the compositor is stuck. Same class of trap: `renderingBackend` unknown-method
errors. Gate any "compositor fault" claim on independent evidence (e.g. its own log timestamps
around a real suspend event), not on errors your own commands generated.

## Secondary environment finding (worth one line when reporting)

`__GL_SYNC_TO_VBLANK=0` exported globally (found via `env | grep GL`) disables NVIDIA vsync
system-wide; combined with KWin `AllowTearing=true` it contributes tearing/jank perception on top
of a real perf fault. Suggest unsetting/removing it only as a secondary cleanup, never as the root
cause.

## Outcome

Root cause judged a firmware/BIOS clock lock on cpu0 (boot BSP); kernel-side fix impossible
(setspeed proved it). Recommended BIOS path: Load Optimized Defaults, EIST/SpeedStep Enabled,
Turbo Boost Enabled, Race-to-Halt Enabled, clear per-core ratio lock on Core 0, then re-verify
`scaling_cur_freq`. Recurrence after reset → BIOS update / CMOS clear.
