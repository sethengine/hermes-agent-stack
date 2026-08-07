---
source: 20260703_231509_6397bb
category: system
date: 2026-07-03
tags: [wifi, power-save, latency, jitter, network]
---

# WiFi Power Save Causes 10-100ms Latency Spikes

WiFi power save mode on interface `wlp131s0f0` causes 10-100ms latency jitter. The radio enters doze state between packets and must wake up before sending/receiving, adding significant delay.

**Symptoms:** Latency spikes in games, choppy streaming, inconsistent ping. `iw dev wlp131s0f0 link` shows `Power save: on`.

**Fix — immediate:**
```
sudo iw dev wlp131s0f0 set power_save off
```

**Fix — permanent:** The `wifi-no-power-save.service` may be enabled but not actually applying the setting. Verify with `systemctl status wifi-no-power-save.service`. Restart or create a custom oneshot:
```
sudo systemctl restart wifi-no-power-save.service
```

**Verification:** `iw dev wlp131s0f0 link | grep "Power save"` should show `off`.

[[manjaro-system-specs-arrow-lake]]
