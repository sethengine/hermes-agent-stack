---
session: 20260502_174824_f53a50
date: 2026-05-02
category: gpu
tags: [nvidia, wayland, kwin, latency, compositor, kde]
---

# KWin Compositor Latency Policy on NVIDIA Wayland

On KDE Plasma 6.5.6 Wayland with NVIDIA RTX 5060 Ti (driver 590.48.01, explicit sync supported), the KWin compositor latency policy significantly affects input responsiveness.

Setting `LatencyPolicy=LowLatency` caused mouse slowdown/deceleration and Alacritty text clipping at 3440x1440@165Hz. Reverting to `MediumLatency` restored stability:

```bash
kwriteconfig5 --file kwinrc --group Compositing --key LatencyPolicy MediumLatency
qdbus org.kde.KWin /Compositor Resume
```

With NVIDIA Wayland + high polling rate mice (1000Hz), LowLatency can overwhelm the compositor leading to buffer underflow. MediumLatency balances snappiness and stability.

## References
- [[corsair-katar-pro-xt-config]]
- [[alacritty-wayland-nvidia-optimization]]
