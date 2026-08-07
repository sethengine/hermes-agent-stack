---
session: 20260702_182552_f2bd10
date: 2026-07-02
category: system
tags: [manjaro, pacman, mirror, pacman-mirrors, fasttrack, network]
---

# Manjaro Pacman Mirror Fix

When a Manjaro mirror goes down, `pacman -Sy` will fail with connection timeouts. The broken mirror (`manjaro.ynh.ovh` in this case) was first in the list, causing all sync operations to fail.

## Fix

Regenerate the mirror list with latency-ranked mirrors:

```bash
sudo pacman-mirrors --fasttrack 5
```

This fetches the official Manjaro mirror pool from `repo.manjaro.org/mirrors.json`, tests each mirror for latency, and writes the top N fastest to `/etc/pacman.d/mirrorlist`.

## Quick Check

Test a specific mirror:

```bash
curl -o /dev/null -s -w "%{http_code}" https://mirror.example.com/manjaro/stable/core/x86_64/core.db
```

A `200` response means the mirror is working; `000` means unreachable.

## References
- [[intel-arrow-lake-kernel-cmdline-tuning]]
- [[nvidia-driver-595-exec-condition-fix]]
