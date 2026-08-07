---
source_session: "20260711_133754_b5c8e4"
date: 2026-07-11
category: gpu
related: [nvidia-edid-firmware-fix, nvidia-edid-fake-nvd-after-sleep]
---

# DP Output Toggle Resume Hook

Replacement for `kscreen-doctor output.mode` in the systemd sleep resume hook that works around the [[nvidia-edid-fake-nvd-after-sleep]] issue.

## Problem

The old resume hook used:
```bash
kscreen-doctor output.DP-3.mode.3440x1440@165
```
This **SIGABRT core dumps** after sleep because 3440×1440@165 doesn't exist in the fake NVD EDID's mode list — the mode set command silently does nothing.

## Solution

Replace with a proper DP output toggle:
```bash
kscreen-doctor output.DP-3.disable
sleep 2
kscreen-doctor output.DP-3.enable
sleep 1
kscreen-doctor output.DP-3.mode.3440x1440@165
```

## Location

`/usr/lib/systemd/system-sleep/latency-fix` — the systemd sleep/resume hook script.

## How It Works

1. Disable DP-3 output (removes the stale 640×480 mode)
2. Wait 2 seconds for the GPU to re-negotiate the DP link
3. Re-enable DP-3 (triggers fresh EDID read — which now returns the real EDID thanks to [[nvidia-edid-firmware-fix]])
4. Wait 1 second for the mode list to populate
5. Set 3440×1440@165 — now available because the real EDID is loaded

Requires both the firmware fix AND the toggle. Neither alone is sufficient.

## ⚠️ Wrap in run_as_user proxy (2026-07-31)

The hook runs as root; bare `kscreen-doctor` calls crash with "no Qt platform plugin could be initialized" because the user's Wayland session env is missing. See [[resume-hook-run-as-user-proxy]] — wrap all display commands in a `runuser` proxy and use `qdbus6` (not `qdbus`, which isn't on root's PATH).
