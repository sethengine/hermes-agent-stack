---
source_session: 20260709_193718_2e6307
category: gpu
tags: [nvidia, wayland, vrr, adaptive-sync, input-lag, kwin, kscreen-doctor]
date: 2026-07-09
---

# VRR/AdaptiveSync on NVIDIA Wayland → Input Lag

VRR (AdaptiveSync) on NVIDIA + Wayland (KWin) is known to cause input lag due to how the NVIDIA driver handles refresh-rate transitions.

## kscreen-doctor Cannot Control VRR

`kscreen-doctor output.DP-3.vrr.on` and `output.DP-3.vrr.off` silently do nothing — unknown settings are accepted with exit 0 but have no effect. kscreen-doctor has no VRR control capability.

## VRR is Controlled via kwinrc

```ini
[Compositing]
VrrPolicy=FullscreenOnly

[Wayland]
AdaptiveSync=true   # toggle VRR on/off here
```

### Toggle commands

```bash
# Disable VRR
kwriteconfig5 --file ~/.config/kwinrc --group Wayland --key AdaptiveSync false
# Enable VRR
kwriteconfig5 --file ~/.config/kwinrc --group Wayland --key AdaptiveSync true
# Restart KWin for change
systemctl --user restart plasma-kwin_wayland.service
```

## Desktop-wide VRR → refresh hunting + Chrome "negative frame latency"

VRR set to **Automatic** (`VrrPolicy=2` + `AdaptiveSync=true`) makes VRR run for *any* window,
including the desktop. On NVIDIA Wayland the refresh rate then hunts up/down and Chrome's display
compositor logs **"Frame latency is negative"** (e.g. `-0.103 ms`, repeated) — frames presented
before ready → the whole desktop feels laggy/janky. The HP X34 VRR floor is ~48 Hz, so when the
desktop drops below 165 you feel it.

**Decisive test (reversible, no full KWin restart):** turn VRR off; if the desktop goes smooth, VRR was it.
```bash
kwriteconfig6 --file kwinrc --group Compositing --key VrrPolicy 0   # 0 = off (test)
qdbus6 org.kde.KWin /Compositor reinitialize 2>/dev/null || qdbus6 org.kde.KWin /Compositor resume
```
Then keep it off, or restrict VRR to fullscreen games only:
```bash
kwriteconfig6 --file kwinrc --group Compositing --key VrrPolicy 3   # 3 = FullscreenOnly
qdbus6 org.kde.KWin /Compositor reinitialize
```
`VrrPolicy` numeric map: `0`=off, `1`=always, `2`=automatic, `3`=fullscreen-only. The `qdbus6` reinit
is far less disruptive than `systemctl --user restart plasma-kwin_wayland.service` (the earlier fix).

## Related

- [[kwin-safety-margin-restore]]
- [[chrome-angle-gl-egl-vs-vulkan-tradeoff]] (Chrome negative-latency is the same symptom family)
- [[nvidia-wayland-display-color-after-sleep]]
- [[nvidia-590-driver-wayland-explicit-sync]]
