---
name: linux-slow-system-triage
description: Diagnose a sluggish Linux box or find an unknown process.
---

# Linux Slow-System Triage (slow box + unknown process)

Use when a user reports SYSTEM-WIDE sluggishness ("everything is slow, all apps + OS") or points at an unknown long-running process ("what is this gunicorn / Python server?") and wants it identified and dealt with. Terse, commands-first.

## Rule 1 — rule out the hardware stall FIRST, cheaply

Run one parallel batch and read the verdicts before any tuning:

```bash
cat /proc/loadavg; grep -c '^processor' /proc/cpuinfo   # load avg << core count = NOT CPU-bound
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
sensors 2>/dev/null | grep -iE 'Package|Core'           # CPU temp
free -h                                                 # ~half free + tiny swap = no mem pressure
vmstat 1 1 | awk 'NR==2{print "iowait wa="$15}'          # wa 0 = NOT I/O-bound
df -h                                                   # near-full fs (Rule 2)
dmesg -T | grep -iE 'i/o error|timeout|Call Trace|out of memory' | tail   # empty = clean
nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,memory.used --format=csv,noheader
```

**Clean = CPU near-idle, ~half RAM free, wa=0, no dmesg errors ⇒ NOT a hardware stall.** Do not over-tune the CPU. Go to Rule 2.

## Rule 2 — the THREE software causes hiding behind clean metrics

1. **Near-full filesystem(s).** `df -h` on ALL mounts, not just `/home`. ext4 near 98% thrashes write allocation → slow fsync, dialogs, `df`, and large writes (Steam update, model pull, Chrome cache); one big write can ENOSPC-stall apps. Target <85%. Also hunt **orphaned git `pack/tmp_pack_*`** (interrupted `git gc`/fetch), often multi-GB and locking the repo.
2. **Stale broken AppImage/FUSE mounts in /tmp.** `mount | grep -i appimage`. A dead `fuse.*AppImage on /tmp/.mount_*` mount (parent AppImage died) returns "Transport endpoint is not connected" and makes `df`, `ls /tmp`, file managers and any filesystem-enumerating tool ERROR or HANG — a classic "everything is slow" symptom. Fix: `fusermount -u /tmp/.mount_* 2>/dev/null || sudo umount -f /tmp/.mount_*`, then relaunch. Expect MULTIPLE entries (one alive + several dead = orphaned launches).
3. **Always-on Docker/container/MCP stack.** `docker ps` — a fleet of containers (Crawl4AI/c4ai, Firecrawl, OpenNotebook, RabbitMQ/Redis/Postgres) up for days spawns supervisord + headless-Chrome + gunicorn workers holding RAM/CPU/VRAM/FDs. Benign but heavy; stop what isn't in use.

**Normalize FD counts:** `/proc/sys/fs/file-nr` (`allocated/limit`) is authoritative — a huge raw `lsof | wc -l` from Chrome/Electron fleets is NORMAL, not a leak. Never report it as root cause.

## Rule 4 — single-core / boot-core clock lock (rules 1-2 clean, still "abysmally slow")

When every subsystem reads healthy (near-idle load, RAM free, wa=0, P0 GPU, clean dmesg) but the user insists everything is *still* glacially slow, the culprit can be **one core pinned to a tiny clock, hidden under aggregate metrics**.

**Probe per-core, not just aggregate:**

```bash
# 1. Dump every core's live frequency:
i=0; for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do \
  echo "cpu$i: $(( $(cat $f) / 1000 )) MHz"; i=$((i+1)); done
#     Look for ONE core (often cpu0 = boot BSP) at ~400-800 MHz while siblings sit at boost (4.6-5.2 GHz).
# 2. It reads BELOW the core's own floor → firmware lock, not idle:
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq   # should be 800000; the core reads 400000
#     Aggregate load average does NOT reveal it (load counts runnable tasks, not per-core speed).
# 3. Prove the OS cannot override it (decisive test):
echo userspace | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor >/dev/null
echo 3000000  | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed >/dev/null
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq     # STILL 400000 ⇒ firmware/BIOS lock
echo performance | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor >/dev/null
# 4. Boot a synthetic load pinned to that core to confirm it fails to boost:
timeout 2 taskset -c 0 bash -c 'while :; do :; done'; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
```

**Why one slow core makes the whole desktop sluggish:** cpu0 is the boot/BSP processor — default target for early-boot interrupts, the scheduler tick, ktimer, and many single-threaded app main loops. A boot core at 1/13th speed throttles input latency, timer ticks, and wakeups system-wide → "everything is slow" even though `uptime`/`loadavg` reads fine.

**Differentiate a firmware lock from Linux-side causes (each is one check):**
- `nvidia-smi -q -d PERFORMANCE,CLOCK` → P0, max clocks = GPU healthy, not the bottleneck.
- `cat /sys/devices/system/cpu/cpu{0,1}/thermal_throttle/*_count` → all 0 = NOT heat/prochot.
- per-core IRQ affinity (`for i in /proc/irq/*; do cat $i/smp_affinity; done` + `systemctl is-active irqbalance`) → affinity spread, none exclusive to cpu0 = not an IRQ-pinning problem.
- `systemctl is-active power-profiles-daemon thermald tuned` → all inactive = no governor override. Upower does NOT set CPU freq.
- `env | grep -iE 'MANGOHUD|LIBGL|GALLIUM'` — absence confirms no forced software-GL fallback.

**Fix is firmware-level, not kernel tuning:** once `userspace`+`setspeed` fails on a core, no sysfs/governor write can raise it. The fix is BIOS/UEFI — Gigabyte Z890: Load Optimized Defaults; Intel SpeedStep/EIST Enabled, Turbo Boost Enabled, Race-to-Halt Enabled, clear any per-core ratio lock on Core 0; reboot and re-check `scaling_cur_freq`. If it recurs after a BIOS reset → stale VCore/firmware state → BIOS update or CMOS clear. Stop hunting kernel tunables as soon as setspeed fails.

**Pitfall — don't chase every log line you probe:** during investigation, DBus calls against KWin's compositor (`dbus-send --dest=org.kde.KWin /Compositor org.kde.kwin.Compositing.active/.suspend/.resume`) print `Error ... No such method` / `Could not find slot ...Adaptor::suspend/resume` into the KWin journal. Those are YOUR OWN failed probes, NOT a real system fault — do not report them as "compositor stuck / suspend-resume failed". Verify a suspicion's cause from *its own* log timestamps, and gate any claim on a check that is independent of the action you took.

## Rule 3 — identify an unknown long-running process (docker/container forensics)

```bash
ps -o pid,ppid,user,etime,args -p <PID>        # user=999 ⇒ container/service account
pstree -ps <PID>                                # surfaces supervisord→gunicorn→chrome chains, container init-parents
grep -E 'docker|container' /proc/<PID>/cgroup  # non-empty ⇒ inside Docker; then `docker ps`
# Probe the exposed listener → reveal the app:
curl -s http://127.0.0.1:<port>/openapi.json | tr ',' '\n' | grep -iE 'title|version'  # e.g. "Crawl4AI API"
curl -s http://127.0.0.1:<port>/docs | grep -oiE '<title>[^<]*'                         # FastAPI swagger
```

`docker ps` names the container (crawl4ai…), `/openapi.json` reveals the real app — answers "what is a gunicorn server?" in two commands.

## Make a daemon run "on demand only" (Ollama pattern)

```bash
sudo systemctl disable --now ollama
systemctl is-active ollama    # inactive
systemctl is-enabled ollama   # disabled
ss -tlnp | grep 11434         # no listener = real proof down
```
Layer `keep_alive=0` so a loaded model unloads between calls — full recipe in the `local-ai-backends` skill.

## References
- `local-ai-backends` skill — Ollama on-demand / keep_alive (the "make it on demand" recipe).
- See `references/session-2026-08-07-sluggish.md` for the original session transcript and the broken-FUSE df error dump.
- See `references/per-core-clock-lock-evidence.md` for the cpu0-400MHz boot-core lock transcript, differential checks, and the KWin dbus-probe red herring.