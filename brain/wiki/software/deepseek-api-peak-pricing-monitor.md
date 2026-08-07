---
source_session: "20260713_192359_e10233"
date: "2026-07-13"
category: software
tags: [deepseek, api, pricing, monitoring, systemd, automation]
---

# DeepSeek API Peak/Valley Pricing Monitor

DeepSeek announced peak-valley pricing starting mid-July 2026. Peak hours (UTC): 01:00–04:00 and 06:00–10:00 — 2× price on all billing items.

## Components

A monitoring system was built with systemd user services:

| Component | Path | Purpose |
|-----------|------|---------|
| CLI status | `~/.local/bin/ds-pricing` | Manual check of current pricing period |
| Daemon | `~/.local/bin/ds-pricing-daemon` | Background notifier, triggers on transitions |
| Systemd service | `~/.config/systemd/user/deepseek-pricing.service` | Oneshot unit run by timer |
| Systemd timer | `~/.config/systemd/user/deepseek-pricing.timer` | Fires every 10 minutes |

## Notification Behavior

The daemon sends KDE desktop notifications only on state changes:

| Event | Notification | Urgency |
|-------|-------------|---------|
| Entering peak | 🔴 Peak Pricing Started | Critical |
| Leaving peak | 🟢 Back to Off-Peak | Normal |
| 15 min before peak | ⚠️ Peak Starting Soon | Critical |

The 10-minute systemd timer runs `ds-pricing-daemon`, which tracks the previous pricing state and only notifies on transitions, avoiding spam on unchanged states.

## Related

- [[llama-server-hermes-config]] — Other API service management
