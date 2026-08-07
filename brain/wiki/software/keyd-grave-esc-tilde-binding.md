---
source_session: "20260703_211056_2e3d4b"
date: "2026-07-03"
category: software
tags: [keyd, keyboard, tilde, esc, key-remapping, systemd]
---

# keyd Grave/Escape Binding Not Active

**Symptom:** keyd config has `grave = esc` in `/etc/keyd/default.conf` but tilde key still types `~`.

**Root cause:** The `keyd.service` was **inactive** — not started and not enabled. The config file was correct, but keyd wasn't running.

**Fix:**
```bash
sudo systemctl start keyd          # apply bindings immediately
sudo systemctl enable keyd         # persist across reboots
```

**Verify:** `sudo keyd monitor` shows raw key presses keyd receives.

**Pattern:** Check service status before assuming the config is wrong. `systemctl is-active keyd` is the first diagnostic step.

[[keyd]] [[key-remapping]] [[systemd-service-fix]]
