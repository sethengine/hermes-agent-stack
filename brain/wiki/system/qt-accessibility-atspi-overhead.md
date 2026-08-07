---
source_session: 20260731_183614_9bd2b1
category: system
date: 2026-07-31
tags: [qt, accessibility, at-spi, overhead, environment.d]
---

# Qt Accessibility Always-On Overhead (at-spi)

## Problem

`/etc/profile.d/qt5-accessibility.sh` sets `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`, which forces the at-spi D-Bus stack (`at-spi-dbus-bus`) to load in every Qt application. Every Qt app pays a small accessibility IPC cost even when no screen reader / assistive tech is in use.

## Fix — disable per-user

```bash
mkdir -p ~/.config/environment.d
printf 'QT_LINUX_ACCESSIBILITY_ALWAYS_ON=0\n' > ~/.config/environment.d/00-a11y-off.conf
```

Takes effect next session. Verify:

```bash
systemctl --user is-active at-spi-dbus-bus   # → inactive
```

## Notes

- No reboot needed — environment.d is applied at next login by the systemd user manager.
- Safe only if you don't use screen readers / assistive tech.
- at-spi was the only extra daemon found in a full system latency audit.

## Related

- [[system-latency-audit-findings]]
- [[kde-plasma-workstation-responsiveness]]
