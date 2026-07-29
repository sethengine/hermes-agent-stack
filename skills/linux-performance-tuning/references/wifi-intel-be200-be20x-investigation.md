# WiFi Investigation — Intel BE200/BE202 (Bz Family) + iwlmld

Session: 2026-07-19, Manjaro kernel 7.0.10, Intel BE202 [Misty Peak]
System: Z890 + Ultra 7 265K + Manjaro KDE Wayland

## Hardware Profile

- **Card**: Intel BE202 160MHz [Misty Peak] — PCI 8086:272b
- **Family**: BZ (IWL_DEVICE_FAMILY_BZ)
- **Driver**: iwlwifi + iwlmld (MLD firmware handler, kernel 6.15+)
- **Firmware**: `iwlwifi-bz-b0-gf-a0-96.ucode.zst` (API v96)
- **PNVM**: `iwlwifi-ma-b0-gf-a0.pnvm.zst`
- **PCIe**: 16 MSI-X queues (IRQ 210-225), NUMA -1, PCI 83:00.0
- **RX/TX**: 2×2 streams, 80 MHz channel width, VHT (WiFi 5/Wave2)

## iwlwifi Module Parameters Discovered

| Param | File | Default | Performance |
|-------|------|---------|-------------|
| `power_save` | iwlwifi | N | N (off) |
| `bt_coex_active` | iwlwifi | Y | N (off when BT soft-blocked) |
| `disable_11be` | iwlwifi | N | Y (avoids unstable WiFi 7 codepaths on Bz rev 1) |
| `uapsd_disable` | iwlwifi | 3 | 3 (bitmask: 1=BSS, 2=P2P Client) |
| `amsdu_size` | iwlwifi | 0 | 0 (default: 12K for multi-RX, 2K for AX210, 4K others) |
| `swcrypto` | iwlwifi | 0 | 0 (hardware crypto) |
| `disable_11n` | iwlwifi | 0 | 0 (no change — HT works fine) |
| `disable_11ac` | iwlwifi | N | N |
| `disable_11ax` | iwlwifi | N | N |
| `power_level` | iwlwifi | 1 | 0 |
| `power_scheme` | **iwlmld** | 2 (BIST) | 1 (CAM — Continuously Aware Mode) |

### Key: iwlmld power_scheme

Found in kernel source `drivers/net/wireless/intel/iwlwifi/mld/power.c`:

```c
int iwl_mld_update_device_power(struct iwl_mld *mld, bool d3) {
    struct iwl_device_power_cmd cmd = {};
    if (iwlmld_mod_params.power_scheme != IWL_POWER_SCHEME_CAM)
        cmd.flags |= cpu_to_le16(DEVICE_POWER_FLAGS_POWER_SAVE_ENA_MSK);
    ...
}
```

- `power_scheme=1` = `IWL_POWER_SCHEME_CAM` — **no power save flags set**, device stays active
- `power_scheme=2` = default (BIST/Balanced) — `POWER_SAVE_ENA_MSK` flag set, PCIe enters L1 substates between traffic bursts

The `POWER_FLAGS_POWER_SAVE_ENA_MSK` controls device-level PCIe power gating — independent from mac80211 power save (`iw dev set power_save on/off`). This is the hidden latency source: even with `iw dev power_save off`, the card still enters L1 substates when power_scheme=2.

## Known BE200/BE202 Instability (ASPM + WiFi 7)

Reference: Blizzke gist (2026-05-05), Intel Community forums, Arch BBS.

**Symptoms**: `iwlwifi: Queue X is stuck`, `NMI_INTERRUPT_UNKNOWN`, 30s system freezes
**Root cause**: ASPM L1 + L1 substates on the BE20x PCIe link cause firmware to not reliably wake under load. On Meteor Lake systems the effect is worse; on Z890 desktop systems it can also trigger.

**Working fix combination** (verified across reports):
1. `iwlwifi disable_11be=1` — avoids unstable WiFi 7 codepaths (EHT/802.11be)
2. `iwlmld power_scheme=1` — CAM mode prevents PCIe L1 transitions
3. PCIe-level ASPM disable via `setpci` for both endpoint + upstream bridge (needed when `Capabilities: <access denied>` is NOT the case; otherwise module params are the only option)

## Path MTU Discovery Methodology

Tested on this system against a router reporting `mtu = 1472` on its WAN side:

```
# Test local gateway at various sizes
ping -M do -c 3 -s <payload> <gateway_ip>
# payload = mtu - 28 (20 IP + 8 ICMP headers)

# Test WAN (end-to-end)
ping -M do -c 3 -s <payload> 8.8.8.8

# Router signals Frag needed with mtu=value:
# From 192.168.0.1 icmp_seq=1 Frag needed and DF set (mtu = 1472)
```

**Result**: Local interface can do MTU 1500 to gateway. WAN path is capped at 1472 by the router. Default interface MTU was 1420 (52 bytes under the real path MTU — ~3.5% overhead saved by setting 1472).

To change MTU temporarily: `sudo ip link set dev wlp131s0f0 mtu 1472`
To persist: add to NetworkManager or netctl config.

## TCP Tuning for WiFi

Settings verified against the 351 Mbit/s / 5ms RTT link budget:

| Sysctl | Value | Why |
|--------|-------|-----|
| `net.ipv4.tcp_congestion_control` | bbr | Best for variable-rate links (WiFi) |
| `net.ipv4.tcp_slow_start_after_idle` | 0 | Prevents cwnd reset after idle gaps |
| `net.ipv4.tcp_mtu_probing` | 1 | Enables PMTU discovery for optimal packet size |
| `net.core.default_qdisc` | fq | Fair queuing for bufferbloat |
| `net.core.rmem_default` | 262144 | BDP for 350Mbps × 5ms ≈ 219KB |
| `net.core.wmem_default` | 262144 | Same as rmem |
| `net.ipv4.tcp_notsent_lowat` | 131072 | Keeps send buffer primed |
| `net.ipv4.tcp_fastopen` | 3 | Reduces connection setup RTT |

## Commands Summary

```bash
# 1. iwlwifi module parameter config (/etc/modprobe.d/iwlwifi.conf)
options iwlwifi power_save=0 bt_coex_active=0 disable_11be=1 uapsd_disable=3
options iwlmld power_scheme=1
# Then: sudo mkinitcpio -P && reboot (Manjaro/Arch)
# Or: sudo update-initramfs -u (Debian/Ubuntu)
# Or: sudo dracut -f (Fedora)

# 2. Path MTU probe
ping -M do -c 3 -s 1444 8.8.8.8   # 1472 MTU probe
ping -M do -c 3 -s 1472 192.168.0.1  # local gateway at 1500

# 3. Set interface MTU
sudo ip link set dev wlpX mtu 1472

# 4. TCP sysctls (/etc/sysctl.d/90-wifi-performance.conf)
net.ipv4.tcp_mtu_probing = 1
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_notsent_lowat = 131072
# Apply: sudo sysctl -p /etc/sysctl.d/90-wifi-performance.conf

# 5. Verify modem info
cat /sys/module/iwlwifi/parameters/*
for f in /sys/module/iwlmld/parameters/*; do echo "$(basename $f)=$(cat $f)"; done

# 6. Verify runtime power save
iw dev wlpX get power_save

# 7. Check link info
iw dev wlpX link
iw dev wlpX station dump
```
