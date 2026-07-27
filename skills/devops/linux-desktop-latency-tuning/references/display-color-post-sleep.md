# Display Color After Sleep — NVIDIA Wayland

## The Problem
After S3 sleep/wake, the DisplayPort link between GPU and monitor re-negotiates. Sometimes the negotiation settles on **limited RGB range (16-235)** instead of **full RGB (0-255)**, causing washed-out colors. This is a GPU firmware-level decision — KDE/KScreen has no control over it on NVIDIA Wayland.

## What KScreen Reports (read-only)
```
kscreen-doctor -o | grep -E 'RgbRange|Color power'
  → RgbRange: unknown           (NVIDIA doesn't expose this via KMS)
  → Color power preference: prefer efficiency and performance
```

## What You Can Do

### DPMS Cycle (forces fresh link negotiation)
```bash
kscreen-doctor --dpms off 2>/dev/null || true
sleep 2
kscreen-doctor --dpms on 2>/dev/null || true
# Re-apply correct mode after wake
kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
```

### Add to Resume Hook
```bash
# In /usr/lib/systemd/system-sleep/latency-fix, after KWin restart:
kscreen-doctor --dpms off 2>/dev/null || true
sleep 2
kscreen-doctor --dpms on 2>/dev/null || true
```

## What You CANNOT Control (NVIDIA Wayland)

| Setting | Available on X11 | Available on Wayland |
|---------|-----------------|---------------------|
| RgbRange (full/limited) | `nvidia-settings` via NV-CONTROL | **No** — driver-internal |
| Color depth / bpc | `nvidia-settings` | **No** — driver-internal |
| DigitalVibrance | `nvidia-settings` | **No** — NV-CONTROL not exposed |
| ColorSpace / ColorRange | `nvidia-settings` | **No** — NV-CONTROL not exposed |
| PowerMizer mode | `nvidia-settings` | **No** — requires X display |

## kscreen-doctor Available Commands

| Command | Effect |
|---------|--------|
| `--dpms off/on` | Power management (Wayland only) |
| `output.NAME.mode.RES@HZ` | Set resolution@refresh |
| `output.NAME.hdr.enable/disable` | Toggle HDR |
| `output.NAME.wcg.enable/disable` | Toggle wide color gamut |
| `output.NAME.iccprofile."/path"` | Apply ICC profile |
| `output.NAME.brightness.N` | Set brightness |

## DPMS State Wake Latencies
- **On**: Normal
- **Standby**: ~1-2s wake
- **Suspend**: ~3-5s wake  
- **Off**: ~5-10s wake

Cycling DPMS off→on forces the monitor and GPU to re-do the full DisplayPort handshake (link training, RGB range, color depth, HDR). This is the most reliable way to restore correct colors after S3 resume on NVIDIA Wayland.
