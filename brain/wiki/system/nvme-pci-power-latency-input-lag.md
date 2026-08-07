---
source_session: 20260709_193718_2e6307
category: system
tags: [nvme, pci, power-management, latency, input-lag, udev]
date: 2026-07-09
---

# NVMe PCI Power Savings → Input Microstutter

Setting NVMe `power/control` to `on` eliminates PCIe link-state wake latency, preventing input microstutter on desktops.

## Mechanism

Linux PCI power control has three modes (`/sys/devices/.../power/control`):

- **`on`** — device always fully powered. No runtime suspend.
- **`auto`** — device can enter D-states when idle. NVMe controller transitions between PS0 (active) and PS1–PS4 (power-save).
- **`auto` + runtime PM** — PCIe link enters L1 on idle.

When a drive in `auto` receives an I/O after idle: PCIe L1 wake (~3-10µs) → NVMe PS2→PS0 transition (~5-50µs) → actual I/O. That **10-60µs wake latency** accumulates on every I/O. For small I/Os triggered by input events (logging on mouse click, texture load on movement), it adds perceptible microstutter.

## Immediate Fix

```bash
# Set specific NVMe to 'on'
echo on | sudo tee /sys/devices/pci0000:00/0000:00:01.0/0000:01:00.0/nvme/nvme0/power/control
```

## Persistent Udev Rule (per-drive)

Match by serial number so only the boot/gaming drive is pinned:

```bash
sudo tee /etc/udev/rules.d/60-nvme-sn850x-nosleep.rules << 'RULE'
ACTION=="add", SUBSYSTEM=="nvme", ATTR{serial}=="24435C4A9C02", ATTR{power/control}="on"
RULE
sudo udevadm control --reload-rules
```

## Trade-off

~1-2W extra power draw at idle (negligible on desktop). Same concept as [[cpu-c-state-latency]] — keeping hardware hot to avoid wake latency.

## Related

- [[system-latency-audit-findings]]
- [[wifi-power-save-latency-spikes]] — same concept applied to networking
- [[post-sleep-optimization-verification]]
