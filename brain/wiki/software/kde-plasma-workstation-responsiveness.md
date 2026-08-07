---
source_session: "20260420_211309_b4bc6a"
category: software
tags: [kde, plasma, workstation, responsiveness, latency, kwin, compositor, kwriteconfig, optimization]
date: 2026-04-20
---

# KDE Plasma Workstation Responsiveness Tweaks

KDE Plasma 6 compositing and animations add visual polish at a latency cost. These tweaks are for raw workstation responsiveness on Manjaro + KDE Wayland + NVIDIA.

## Compositor — Disable Effects (biggest win)

```bash
kwriteconfig5 --file kwinrc --group Compositing --key Enabled false
qdbus org.kde.KWin /KWin reconfigure
```

Re-enable with `Enabled=true` and restart. Disabling compositor effects cuts 20–50% from perceived latency on window moves and app switching.

## Window Management

```bash
kwriteconfig5 --file kwinrc --group Windows --key BorderlessMaximizedWindows true
kwriteconfig5 --file kwinrc --group Windows --key MaximizeToCurrentScreen false
kwriteconfig5 --file kwinrc --group Windows --key Placement Smart
kwriteconfig5 --file kwinrc --group Windows --key SnapOnlyWhenOverlapping true
qdbus org.kde.KWin /KWin reconfigure
```

- **BorderlessMaximizedWindows=true** — removes title bar on maximized windows (more screen space)
- **SnapOnlyWhenOverlapping=true** — instant quarter/50/25% tiles
- **Placement=Smart** — cascading windows avoid overlap

## KDE Globals

```bash
kwriteconfig5 --file kdeglobals --group Effects --key Enable false
kwriteconfig5 --file kdeglobals --group KWin --key BorderSnapZone 5
kwriteconfig5 --file kdeglobals --group Windows --key DelayFocusInterval 100
qdbus org.kde.plasmashell /PlasmaShell recompileDesktopTooling
```

- **BorderSnapZone=5** — tiny snap zone (resist accidental snapping)
- **DelayFocusInterval=100** — faster focus following mouse

## Plasma Panel Optimization

Panels consume compositor resources. Minimize them:

```bash
# Lock panels (prevent resize handles)
kwriteconfig5 --file plasmashellrc --group PlasmaViews --group Panel\ 1 --key floating false
# Disable unused autostart items
kwriteconfig5 --file plasma-workspace --group PlasmaAutostart --key HideFromUser plasma-thunderbolt
```

Manual: Right-click Panel > Edit Panel → uncheck "Allow resizing", set Length=Fixed (min), Opacity=100%.

## Animation Speed

```bash
kwriteconfig5 --file kwinrc --group Compositing --key AnimationSpeed 0
qdbus org.kde.KWin /KWin reconfigure
```

Sets all animations to instant.

## Latency Policy Toggle

```bash
# For multitasking responsiveness
kwriteconfig5 --file kwinrc --group Compositing --key LatencyPolicy HighThroughput
# For single-app low-latency (gaming)
kwriteconfig5 --file kwinrc --group Compositing --key LatencyPolicy ExclusiveFrametime
qdbus org.kde.KWin /KWin reconfigure
```

## Baloo (File Indexing)

```bash
balooctl disable
balooctl purge
```

Baloo indexing consumes CPU and I/O during file operations on large filesystems.

## SDDM HiDPI

```bash
sudo sed -i 's/EnableHiDPI=false/EnableHiDPI=true/' /etc/sddm.conf
sudo systemctl restart sddm
```

## Sysctl Low-Latency

```bash
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.d/99-lowlatency.conf
echo 'kernel.sched_rt_runtime_us=-1' | sudo tee -a /etc/sysctl.d/99-lowlatency.conf
sudo sysctl --system
```

## Related

[[kwin-systemd-environment-vars]] — env vars for kwin
[[nvidia-wayland-kwin-latency-policy]] — LatencyPolicy details
[[kwin-safety-margin-restore]] — DRM safety margin
[[kde-baloo-runner-disable]] — Baloo disable
