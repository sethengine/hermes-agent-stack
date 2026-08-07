#!/bin/bash
# extract_keys.sh — Step 1 of the audit. Extracts the EXACT key list from the
# live system into ./batches/ so a future resume never re-derives from context.
# Usage: bash extract_keys.sh   (run from the audit working dir, e.g. ~/audit)
set -u
mkdir -p batches baseline configs fixes
echo "=== extracting sysctl groups ==="
sysctl -a 2>/dev/null > batches/all_sysctl.txt
for g in kernel vm fs net core user dev debug abi; do
  sysctl -a 2>/dev/null | grep -E "^${g}\." | sort > "batches/${g}.list"
done
# net.core / net.ipv4 / net.ipv6 globals (explicit, NOT per-interface)
{
  sysctl -a 2>/dev/null | grep -E "^net\.core\."
  sysctl -a 2>/dev/null | grep -E "^net\.ipv4\." | grep -vE "^net\.ipv4\.conf\.[a-z0-9]"
  sysctl -a 2>/dev/null | grep -E "^net\.ipv6\." | grep -vE "^net\.ipv6\.conf\.[a-z0-9]"
} | sort -u > batches/net_global.list
echo "  net globals: $(wc -l < batches/net_global.list)"
# per-interface conf keys (summarized later, not row-per-key)
sysctl -a 2>/dev/null | grep -E "^net\.(ipv4|ipv6)\.conf\.[a-z0-9]+\." > batches/net_periface.list
echo "  net per-interface: $(wc -l < batches/net_periface.list)"

echo "=== extracting cmdline ==="
cat /proc/cmdline | tr ' ' '\n' | grep -v '^$' > baseline/cmdline.txt
echo "  cmdline tokens: $(wc -l < baseline/cmdline.txt)"

echo "=== extracting /sys/kernel writable ==="
: > baseline/sys_kernel.txt
for f in /sys/kernel/*; do [ -w "$f" ] 2>/dev/null && echo "$(basename $f)=$(cat $f 2>/dev/null | tr '\n' ' ' | cut -c1-120)" >> baseline/sys_kernel.txt; done
echo "  sys_kernel keys: $(wc -l < baseline/sys_kernel.txt)"

echo "=== extracting THP ==="
{
  for k in enabled defrag shmem_enabled use_zero_page shrink_underused hpage_pmd_size; do
    echo "$k = $(cat /sys/kernel/mm/transparent_hugepage/$k 2>/dev/null)"
  done
} > baseline/thp.txt

echo "=== extracting cpu per-core + cpuidle ==="
: > baseline/cpu_percore.txt
: > baseline/cpuidle_disable.txt
for c in /sys/devices/system/cpu/cpu[0-9]*; do
  n=${c##*cpu}
  gov=$(cat $c/cpufreq/scaling_governor 2>/dev/null)
  epp=$(cat $c/cpufreq/energy_performance_preference 2>/dev/null)
  echo "cpu$n gov=$gov epp=$epp" >> baseline/cpu_percore.txt
  dis=$(cat $c/cpuidle/state2/disable 2>/dev/null)
  echo "cpu$n: disable=$dis" >> baseline/cpuidle_disable.txt
done

echo "=== extracting block IO queue ==="
: > baseline/block_queue.txt
for d in /sys/block/*; do
  n=$(basename $d)
  echo "=== $n ===" >> baseline/block_queue.txt
  for q in scheduler nr_requests read_ahead_kb wbt_lat_usec rotational rq_affinity nomerges; do
    v=$(cat $d/queue/$q 2>/dev/null | tr '\n' ' ')
    echo "$q = $v" >> baseline/block_queue.txt
  done
done

echo "=== extracting cgroup v2 (user.slice) ==="
{
  echo "controllers: $(cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null)"
  echo "subtree_control: $(cat /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null)"
  for f in cpu.max cpu.weight memory.max memory.high memory.swap.max pids.max; do
    echo "user.slice/$f = $(cat /sys/fs/cgroup/user.slice/$f 2>/dev/null)"
  done
} > baseline/cgroup.txt

echo "=== copying config files ==="
mkdir -p configs/modprobe configs/environment.d configs/udev/rules configs/udev/hwdb
cp /etc/modprobe.d/*.conf configs/modprobe/ 2>/dev/null
cp /etc/environment configs/environment 2>/dev/null
cp /etc/environment.d/* configs/environment.d/ 2>/dev/null
cp ~/.config/kwinrc configs/kwinrc 2>/dev/null || cp /etc/kwinrc configs/kwinrc 2>/dev/null
cp /etc/gamemode.ini configs/gamemode.ini 2>/dev/null
cp /etc/default/grub configs/grub 2>/dev/null
cp /usr/lib/systemd/system-sleep/latency-fix configs/latency-fix 2>/dev/null
cp /usr/local/sbin/pin-irqs-dynamic configs/pin-irqs-dynamic 2>/dev/null || find / -name 'pin-irqs*' -exec cp {} configs/pin-irqs-dynamic \; 2>/dev/null
cp /etc/docker/daemon.json configs/docker-daemon.json 2>/dev/null
cp ~/.zshrc configs/zshrc 2>/dev/null
mkdir -p configs/udev/rules configs/udev/hwdb
cp /etc/udev/rules.d/*.rules configs/udev/rules/ 2>/dev/null
cp /etc/udev/hwdb.d/*.hwdb configs/udev/hwdb/ 2>/dev/null
echo "DONE. Keys extracted to ./batches/ and ./baseline/."
