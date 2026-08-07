---
source: "20260711_143618_f492c9,20260502_150358_5e17d2"
category: system
date: 2026-07-11
tags: [nvidia, wayland, cursor, hardware, WLR_NO_HARDWARE_CURSORS, zshrc]
---

# NVIDIA Wayland Hardware Cursors Configuration

The environment variable `WLR_NO_HARDWARE_CURSORS` controls whether Wayland compositors use GPU hardware cursors or software-rendered cursors on NVIDIA.

## Where It's Set

| File | Line | Value | Status |
|------|------|-------|--------|
| `~/.zshrc` | 182 | `export WLR_NO_HARDWARE_CURSORS=1` | **Active** |
| `/etc/environment.d/99-nvidia-wayland.conf` | 4 | `#WLR_NO_HARDWARE_CURSORS=1` | Commented out |

Only `~/.zshrc` is actively setting it. The system-wide file has it commented, so shell-dependent.

## Implication

Setting `WLR_NO_HARDWARE_CURSORS=1` disables hardware cursor acceleration, which avoids GPU cursor-plane bugs on NVIDIA but uses more compositing resources. If the user logs in through a display manager (not from terminal + startplasma-wayland), `~/.zshrc` may not be sourced, and the var won't take effect. A system-wide config in `/etc/environment.d/` or `~/.config/environment.d/` would be more reliable.
