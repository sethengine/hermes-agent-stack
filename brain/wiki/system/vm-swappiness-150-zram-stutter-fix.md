---
source_session: 20260731_183614_9bd2b1
date: 2026-07-31
category: system
title: vm.swappiness=150 zram swap causes Dota2/desktop stutter
---

# vm.swappiness=150 forcing zram swap → input lag & stutter

**Root cause:** `vm.swappiness = 150` is active at runtime even though RAM is plentiful
(38 GB free). The kernel eagerly swaps anonymous pages into **zram compressed swap**,
causing page-fault stalls (decompress on touch) = stutter in Dota2 + lag on the desktop.
Live proof during the session: Dota2 had **1.25 GB in zram**, system had swapped 8 GB total,
yet 38 GB RAM was free.

The static sysctl files say 10/100/60 — something **overrides to 150 at runtime**, likely
`/etc/sysctl.d/90-wifi-performance.conf` (unreadable) or the zram setup; a later file wins.

**Fix (immediate + persistent + evacuate):**
```bash
# 1. Stop eager swapping now
echo 10 | sudo tee /proc/sys/vm/swappiness

# 2. Persist — later file wins over the 150 writer
sudo tee /etc/sysctl.d/99-swappiness-low.conf <<'EOF'
vm.swappiness = 10
EOF
sudo sysctl --system

# 3. Evacuate the 8GB already in zram back to RAM (free=38GB, safe)
sudo swapoff /dev/zram0 && sudo swapon /dev/zram0
swapon --show        # zram0 USED should now be ~0

# 4. Verify
cat /proc/sys/vm/swappiness                                  # 10
grep -E 'VmSwap' /proc/$(pgrep -f 'dota2' | head -1)/status   # ~0 after playing
```

**Secondary finding:** `kwin_wayland` sustained ~13% CPU (35:51 CPU time in 4:44 uptime)
compositing at 165 Hz. Before/while gaming, close GPU-using apps you don't need
(omniroute, zed, opencode desktop) to free the compositor thread. (Vulkan backend skipped —
it segfaulted before.)

## ⚠️ Permanent zram removal (the swapoff above is NOT persistent)

`swapoff /dev/zram0 && swapon /dev/zram0` only clears it for the current boot. At next boot the
zram-generator recreates it (CachyOS ships `/usr/lib/systemd/zram-generator.conf`; no `/etc` override
exists, and `/run/systemd/generator/dev-zram0.swap` is already queued). With 64 GB RAM, zram is pure
loss — it only compressed 8 GB of RAM and put 1.25 GB of Dota in it. Kill it for good:

```bash
# Empty /etc config overrides the /usr/lib one → generator creates NO zram devices
sudo touch /etc/systemd/zram-generator.conf
# Belt-and-suspenders: mask the per-device unit so nothing can start it
sudo systemctl mask systemd-zram-setup@zram0.service

# Verify after reboot (both must print nothing / only the disk swap):
ls /run/systemd/generator/ | grep zram      # → no output
swapon --show                              # → only nvme1n1p2
```

Final memory setup for 64 GB: **RAM + 15.6 GB disk swap for emergencies, swappiness 10** → kernel
never swaps unless genuinely out of memory. The `vm.swappiness=10` is held by a shadowed udev rule.

See also: [[system-latency-audit-findings]] (notes swappiness 5-vs-10 file conflict),
[[dota2-vulkan-launch-optimization]] (zram micro-stutter), [[kde-plasma-workstation-responsiveness]],
[[sysctl-config-conflicts-latency]].
