#!/bin/bash
# Full baseline collector for an exhaustive "every parameter" Linux audit.
# Collects the CURRENT value of every tunable surface to /home/sethengine/audit/baseline/
# then hand those files to a research subagent so it doesn't hold thousands of values in context.
#
# Usage: bash collect_baseline.sh
# sudo bits (sched_features) are best-effort: if sudo prompts and cant be satisfied,
# sched_features.txt will contain NEEDS_ROOT — have the subagent try again or note it.

D="${1:-/home/sethengine/audit}"
mkdir -p "$D/baseline" "$D/baseline/modprobe" "$D/baseline/udev/rules" "$D/baseline/udev/hwdb" "$D/baseline/configs"

# S1 kernel command line
cat /proc/cmdline > "$D/baseline/cmdline.txt"

# S2 all sysctl (ALL, including 3300 per-interface net.*)
sysctl -a 2>/dev/null > "$D/baseline/all_sysctl.txt"

# S3 /sys/kernel writable tunables
: > "$D/baseline/sys_kernel.txt"
for f in /sys/kernel/*; do
  [ -f "$f" ] || continue
  val=$(cat "$f" 2>/dev/null)
  printf "%s = %s\n" "$(basename "$f")" "${val//$'\n'/ }" >> "$D/baseline/sys_kernel.txt"
done

# S4 debugfs sched features (needs root)
sudo cat /sys/kernel/debug/sched/features 2>/dev/null > "$D/baseline/sched_features.txt" || echo "NEEDS_ROOT" > "$D/baseline/sched_features.txt"

# S5 per-core cpufreq + cpuidle
: > "$D/baseline/cpu_percore.txt"
for c in /sys/devices/system/cpu/cpu[0-9]*; do
  n=${c##*/}
  gov=$(cat "$c/cpufreq/scaling_governor" 2>/dev/null)
  epp=$(cat "$c/cpufreq/energy_performance_preference" 2>/dev/null)
  printf "%s gov=%s epp=%s\n" "$n" "$gov" "$epp" >> "$D/baseline/cpu_percore.txt"
done

# S6 block queue tunables
: > "$D/baseline/block_queue.txt"
for d in /sys/block/*/; do
  name=$(basename "$d")
  echo "=== $name ===" >> "$D/baseline/block_queue.txt"
  for q in scheduler nr_requests read_ahead_kb wbt_lat_usec rotational rq_affinity nomerges iosched*; do
    v=$(cat "$d/queue/$q" 2>/dev/null)
    [ -n "$v" ] && echo "$q = $v" >> "$D/baseline/block_queue.txt"
  done
done

# S7 cgroup v2 (controllers + user.slice limits)
: > "$D/baseline/cgroup.txt"
echo "controllers: $(cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null)" >> "$D/baseline/cgroup.txt"
echo "subtree_control: $(cat /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null)" >> "$D/baseline/cgroup.txt"
for f in cpu.max cpu.weight memory.max memory.high memory.swap.max pids.max; do
  v=$(cat "/sys/fs/cgroup/user.slice/$f" 2>/dev/null)
  [ -n "$v" ] && echo "user.slice/$f = $v" >> "$D/baseline/cgroup.txt"
done

# S8 modprobe.d all fragments
for f in /etc/modprobe.d/*.conf; do
  [ -f "$f" ] || continue
  echo "===== $f =====" >> "$D/baseline/modprobe/$(basename "$f")"
  cat "$f" >> "$D/baseline/modprobe/$(basename "$f")"
done

# S9 configs (User base for a KDE/NVIDIA/Docker system; adjust paths as needed)
for src in \
  "$HOME/.config/kwinrc" /etc/gamemode.ini /etc/environment "$HOME/.zshrc" /etc/docker/daemon.json \
  /etc/default/grub /usr/lib/systemd/system-sleep/latency-fix /usr/local/bin/pin-irqs-dynamic; do
  [ -f "$src" ] && cp "$src" "$D/baseline/configs/$(basename "$src")" 2>/dev/null
done
[ -d /etc/environment.d ] && cp -r /etc/environment.d "$D/baseline/configs/environment.d" 2>/dev/null

# S10 udev rules + hwdb
for f in /etc/udev/rules.d/*.rules; do [ -f "$f" ] && cp "$f" "$D/baseline/udev/rules/"; done
for f in /etc/udev/hwdb.d/*.hwdb; do [ -f "$f" ] && cp "$f" "$D/baseline/udev/hwdb/"; done

# S11 THP all knobs
: > "$D/baseline/thp.txt"
for f in /sys/kernel/mm/transparent_hugepage/*; do
  [ -f "$f" ] || continue
  echo "$(basename "$f") = $(cat "$f" 2>/dev/null | tr '\n' ' ')" >> "$D/baseline/thp.txt"
done

echo "COLLECTION DONE into $D/baseline/ — $(wc -l "$D/baseline"/*.txt 2>/dev/null | tail -1)"