---
source: "20260719_162337_17012c"
date: "2026-07-19"
category: "system"
tags: [intel, be202, wifi, iwlwifi, iwlmld, network, performance, manjaro]
wiki-links: [wifi_power_save_latency_spikes, network_powersave_resume_config]
---

# Intel BE202 WiFi 7 Optimization (iwlwifi)

Intel BE202 (Misty Peak, PCI ID `8086:272b`) WiFi 7 combo card on Manjaro Linux. Driver stack: `iwlwifi` + `iwlmld` (MLD firmware handler), firmware API v96.

## Module Parameters (`/etc/modprobe.d/iwlwifi.conf`)

```conf
options iwlwifi power_save=0 bt_coex_active=0 disable_11be=1 uapsd_disable=3
options iwlmld power_scheme=1
```

| Parameter | Effect |
|-----------|--------|
| `power_save=0` | Disable all firmware power saving |
| `bt_coex_active=0` | Disable Bluetooth coexistence (BE202 is combo card) — avoids wasting airtime on BT that's soft blocked |
| `disable_11be=1` | Disable WiFi 7 (802.11be) early — avoids beta firmware path, falls back to WiFi 6E |
| `uapsd_disable=3` | Disable U-APSD for both AC and non-AC clients |
| `power_scheme=1` (iwlmld) | CAM (Continuous Active Mode) |

## Sysctl Tweaks (`/etc/sysctl.d/90-wifi-performance.conf`)

```ini
net.ipv4.tcp_mtu_probing = 1
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_notsent_lowat = 131072
```

## MTU Tuning

Path MTU probe to `8.8.8.8` found real path MTU is **1472** (WAN side caps it), not 1500. Previous config had 1420 — 52 bytes under. Bumped to 1472 via NetworkManager config for `aridren_5G`.

## RF Kill Note

`rfkill block bluetooth` kills the combo card's BT radio at kernel level. Even soft-blocked BT (`Soft blocked: yes`) still runs coexistence firmware arbitration. Hard block reclaims airtime for WiFi. Not applied in this session (user rejected).

## Related
- [[wifi_power_save_latency_spikes]]
- [[network_powersave_resume_config]]
