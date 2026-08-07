# zram / Swap / udev / sysctl Audit — Session Transcript (2026-08)

Dota2 stutter + desktop input lag investigation on 64 GB Manjaro/CachyOS-kernel system
(Z890, Arrow Lake Ultra 7 265K, RTX 5060 Ti, KDE Wayland). The game was pinned to P-cores,
GPU at 5% / 952 MHz / P1, yet stuttering. Root cause was NOT the GPU — it was memory.

## Root cause chain

1. CachyOS ships `zram-generator` (`/usr/lib/systemd/zram-generator.conf`, zram-size=ram)
   → creates `/dev/zram0` as swap at boot.
2. `/usr/lib/udev/rules.d/30-zram.rules` sets `SYSCTL{vm.swappiness}="150"` on zram init.
3. With 64 GB RAM, swappiness=150 made the kernel aggressively compress pages into zram:
   - Dota2 had 1.25 GB of its memory in zram while 38 GB RAM was free
   - 8 GB total had been swapped into zram
   - Result: stutter + input lag even with game pinned to P-cores.

## Why "I changed the rule but swappiness is still 150"

- udev loads rules at EVENT time, not file-write time. Boot already happened with the old rule.
- `udevadm trigger` re-fires the rule files CURRENTLY installed — if the 150 rule still exists
  in /usr/lib, trigger re-applies 150. The /etc shadow (same filename) runs after and wins.
- Required sequence: write shadow rule → `sudo udevadm control --reload` → trigger/replug.

## Permanent removal (64 GB system — zram is pointless)

```bash
sudo tee /etc/udev/rules.d/30-zram.rules <<'EOF'
ACTION=="change", KERNEL=="zram0", ATTR{initstate}=="1", SYSCTL{vm.swappiness}="10"
EOF
sudo udevadm control --reload
sudo swapoff /dev/zram0
sudo systemctl mask systemd-zram-setup@zram0.service
sudo touch /etc/systemd/zram-generator.conf    # empty /etc config disables generator
```

Verification (after reboot): `swapon --show` → only the disk partition;
`ls /run/systemd/generator/ | grep zram` → empty.

## Broken udev rules found (harmless but noisy)

Detected via `journalctl -b | grep 'udev-worker.*Could not chase'` then aggregating rule:line.

| Rule | Error cause | Effect |
|------|-------------|--------|
| `60-iosched.rules:1` KERNEL=="nvme[0-9]*" | matches nvme0 controller; `queue/scheduler` only exists on namespace nvme0n1 | scheduler never set; kernel default is already `none` — no harm |
| `60-readahead.rules:1` same pattern | same controller/namespace mismatch | read_ahead_kb never set |
| `50-usb-input-latency.rules:2` | `power/autosuspend` doesn't exist on USB interfaces (only on device) | redundant with GRUB `usbcore.autosuspend=-1` |
| `90-keyboard-noautosuspend.rules` | same interface issue + 3 duplicate Corsair lines | redundant; dedupe |

Fix pattern for NVMe rules: match the namespace — `KERNEL=="nvme[0-9]n[0-9]*"`.
Per-device USB autosuspend rules are unnecessary when `usbcore.autosuspend=-1` is in GRUB.

## sysctl.d silent override cases

Runtime values disagreed with the "intended" file:

| Key | Expected source | Runtime | Overridden by |
|-----|-----------------|---------|---------------|
| vm.vfs_cache_pressure | 99-performance.conf + cachyos = 50 | 100 | 99-workstation.conf = 100 (later wins) |
| vm.max_map_count | 10-manjaro.conf = 1048576 | 262144 | 99-performance.conf = 262144 (later wins) |
| vm.swappiness | 10 (shadowed rule) | 10 | fixed via udev shadow, not sysctl.d |

Rule: sysctl.d applies files in lexical order; the LAST file per key wins. Always
`sysctl <key>` + `grep -rn '<key>' /etc/sysctl.d/ /usr/lib/sysctl.d/`.

## Dead sysctl keys on kernel 7.x (EEVDF)

`kernel.sched_child_runs_first`, `kernel.pressure_stall.max_*` — removed; writes fail with
"No such file or directory" (log noise only). Safe to delete from sysctl.d.

## Verified-correct latency sysctl set

```
vm.swappiness=10 · vm.page-cluster=0 · kernel.sched_rt_runtime_us=-1
kernel.sched_autogroup_enabled=0 · kernel.timer_migration=0 · kernel.nmi_watchdog=0
kernel.ftrace_enabled=0 · kernel.numa_balancing=0 · kernel.printk=3 3 3 3
net.ipv4.tcp_low_latency=1 · tcp_early_demux=1 · tcp_early_retrans=3 · tcp_mtu_probing=1
tcp_congestion_control=bbr · default_qdisc=fq_codel · vm.zone_reclaim_mode=0
```
