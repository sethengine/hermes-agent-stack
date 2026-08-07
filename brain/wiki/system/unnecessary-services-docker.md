---
source: 20260703_231509_6397bb
category: system
date: 2026-07-03
tags: [docker, containerd, services, resource-waste, systemd]
---

# Unnecessary Docker Services Waste Resources

Docker services (`docker.socket`, `docker`, `containerd`) consume system resources even when no containers are running. On a desktop system that only occasionally uses Docker, these services run pointlessly at boot.

**Impact:** Memory and CPU for daemon processes, network bridges (docker0, br-* interfaces) consume kernel resources, socket activation keeps systemd units loaded.

**Fix — stop immediately:**
```
sudo systemctl stop docker.socket docker containerd
```

**Fix — disable auto-start:**
```
sudo systemctl disable --now docker.socket docker containerd
```

**Cleanup network interfaces:**
```
sudo docker network prune -f
sudo ip link delete docker0 2>/dev/null
sudo ip link delete br-* 2>/dev/null
```

**Re-enable when needed:** `sudo systemctl enable --now docker` starts the full stack on demand.
