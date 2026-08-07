---
source: 20260502_150358_5e17d2
category: gpu
date: 2026-07-06
tags: [nvidia, wayland, sleep, display, color, dpms, rgb-range]
---

# NVIDIA Wayland Display Color Degradation After S3 Sleep

After S3 sleep/wake on NVIDIA + Wayland, display colors can degrade because the DisplayPort link re-negotiates with the monitor. Known issues:

- RGB range resets from **full (0–255)** to **limited (16–235)** → washed-out colors
- Color depth drops from **10-bit** to **8-bit**
- EDID color profile can be lost

**RgbRange** and color depth are NVIDIA driver internals not exposed via KMS — KDE/kscreen cannot query or set them directly. The effective workaround is cycling DPMS after resume to force a fresh DisplayPort handshake (monitor re-reads EDID, GPU re-negotiates link params).

## Fix — DPMS cycle in resume hook

```bash
kscreen-doctor --dpms off 2>/dev/null || true
sleep 2
kscreen-doctor --dpms on 2>/dev/null || true
kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
```

Add to `/usr/lib/systemd/system-sleep/latency-fix` after KWin restart.

## References
- [[dpms-display-power-management-signaling]]
- [[nvidia-wayland-kwin-latency-policy]]
