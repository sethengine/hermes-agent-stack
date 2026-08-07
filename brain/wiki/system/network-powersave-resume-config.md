---
source_session: 20260712_182512_850b41
date: 2026-07-13
category: system
tags: [wifi, network, powersave, iwlwifi, iwlmld, resume, sleep, networkmanager]
---

# WiFi Power Save and Network Performance Tuning

## Problem

WiFi power save re-enables after S3 sleep/resume despite NetworkManager configuration, causing latency spikes and reduced throughput.

## Root Cause

- `iwlmld` (the newer Intel WiFi driver) uses `power_scheme=2` (balanced) by default
- Power save is reset on resume even when NM `wifi.powersave=2` is configured
- The radio power-saving introduces latency (up to 100ms+) for gaming/real-time workloads

## Fix 1 — Modprobe Config (persists across boots)

```sh
echo 'options iwlwifi power_save=0 uapsd_disable=1
options iwlmld power_scheme=1' | sudo tee /etc/modprobe.d/iwlwifi.conf
```

Apply immediately without reboot:
```sh
sudo sh -c 'echo 1 > /sys/module/iwlmld/parameters/power_scheme'
```

## Fix 2 — NetworkManager Dispatcher (catches post-resume)

Create `/etc/NetworkManager/dispatcher.d/90-wifi-powersave-off`:

```bash
#!/bin/bash
if [[ "$2" == "up" && "$1" =~ ^wl ]]; then
    iw dev "$1" set power_save off 2>/dev/null || true
fi
```

```sh
sudo chmod 755 /etc/NetworkManager/dispatcher.d/90-wifi-powersave-off
```

This runs `iw set power_save off` every time the WiFi interface comes up (boot, resume, reconnect).

## ⚠️ Fix 3 — NM conf silently re-enables power save (2026-07-31)

Even with the dispatcher active, NM re-applies its own setting on every network reconnect:

```
/etc/NetworkManager/conf.d/wifi-powersave.conf:  wifi.powersave = 3     # 3 = ENABLE
```

Value 3 (enable) overrides any `iw set power_save off` on reconnect → intermittent WiFi latency. Fix permanently:

```bash
sudo sed -i 's/wifi.powersave = 3/wifi.powersave = 2/' /etc/NetworkManager/conf.d/wifi-powersave.conf
sudo systemctl restart NetworkManager
iw dev wlp131s0f0 get power_save        # verify: off (persists across reconnects)
```

`wifi.powersave = 2` = disable (1 = ignore, 2 = disable, 3 = enable).

## Verification

```sh
iw dev wlp131s0f0 get power_save       # should show "Power save: off"
cat /sys/module/iwlmld/parameters/power_scheme  # should show 1 (active)
```

## Related

- [[post-sleep-optimization-verification]] — broader post-sleep checklist
- [[nvidia-595-suspend-resume-workaround]] — GPU-related sleep issues
