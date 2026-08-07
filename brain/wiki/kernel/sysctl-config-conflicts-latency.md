---
source_session: 20260731_183614_9bd2b1
date: 2026-07-31
category: kernel
title: sysctl config conflicts causing latency/responsiveness regressions
---

# sysctl config conflicts (own configs fighting each other)

Found during a full latency audit on Manjaro+CachyOS sysctl layering. After the swappiness fix, nothing here causes active input lag, but each is a real regression worth correcting.

## 1. vm.vfs_cache_pressure: 100 vs intended 50
`99-performance.conf` (and CachyOS base) set `50`, but `99-workstation.conf` overrides to `100` (kernel default). Kernel drops dentry/inode cache aggressively → disk re-reads → occasional lag spikes.

```bash
sudo sed -i 's/^vm.vfs_cache_pressure = 100/vm.vfs_cache_pressure = 50/' /etc/sysctl.d/99-workstation.conf
sudo sysctl -w vm.vfs_cache_pressure=50
```

## 2. vm.max_map_count: 262144 vs Manjaro default 1048576
`99-performance.conf` overrides the Manjaro default to `262144` → games/emulators can hit the map limit and fail allocations.

```bash
sudo sed -i 's/^vm.max_map_count=262144/vm.max_map_count=1048576/' /etc/sysctl.d/99-performance.conf
sudo sysctl -w vm.max_map_count=1048576
```

## 3. Softlockup watchdog (optional micro-jitter win)
`nmi_watchdog` already off; killing the per-core softlockup threads removes the last periodic wakeup.

```bash
sudo tee /etc/sysctl.d/99-watchdog.conf <<'EOF'
kernel.nmi_watchdog = 0
kernel.watchdog = 0
EOF
sudo sysctl -w kernel.watchdog=0
```

## 4. netdev_budget_usecs: 4000 → 2000 (online games)
2x-default softirq budget (4000µs) can hog 4ms/round on E-cores (NIC pinned 14-19). Tighten for less network-induced jitter.

```bash
sudo sed -i 's/net.core.netdev_budget_usecs = 4000/net.core.netdev_budget_usecs = 2000/' /etc/sysctl.d/99-performance.conf
sudo sysctl -w net.core.netdev_budget_usecs=2000
```

Related: [[vm-swappiness-150-zram-stutter-fix]], [[cpu-min-perf-pct-systemd-permanent]], [[kde-plasma-workstation-responsiveness]]
