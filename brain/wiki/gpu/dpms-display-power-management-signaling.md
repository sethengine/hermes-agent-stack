---
source: 20260502_150358_5e17d2
category: gpu
date: 2026-07-06
tags: [dpms, display, power-management, monitor, nvidia, wayland]
---

# DPMS — Display Power Management Signaling

DPMS is the VESA standard controlling monitor power states over DisplayPort/HDMI:

| State | Behavior | Wake time |
|-------|----------|-----------|
| On | Normal operation | — |
| Standby | Blank screen, circuits warm | ~1–2s |
| Suspend | Most circuits off | ~3–5s |
| Off | Deepest sleep, near-zero power | ~5–10s |

Cycling DPMS (`off → on`) forces a full DisplayPort link re-negotiation between GPU and monitor — the monitor re-reads EDID, GPU re-negotiates color range, depth, link speed, and HDR state.

## Use case: post-sleep color restoration

After S3 sleep, NVIDIA's DisplayPort link can resume in a degraded state (limited RGB, lower bpc). A DPMS cycle forces a fresh handshake that usually restores the correct color settings without rebooting.

```bash
kscreen-doctor --dpms off
sleep 2
kscreen-doctor --dpms on
```

## References
- [[nvidia-wayland-display-color-after-sleep]]
