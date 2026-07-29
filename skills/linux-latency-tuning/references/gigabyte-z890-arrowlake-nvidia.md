# Session-Specific: Gigabyte Z890 + Arrow Lake 265K + RTX 5060 Ti + KDE 6.5.6 Wayland

## Hardware
- **Motherboard**: Gigabyte Z890 AERO G (BIOS F17f)
- **CPU**: Intel Core Ultra 7 265K (20-core Arrow Lake, no SMT)
- **GPU**: NVIDIA RTX 5060 Ti (driver 595.71.05)
- **Monitor**: HP X34 3440x1440@165Hz
- **RAM**: 64GB
- **Storage**: WD SN850X 2TB + Kingston 1TB (both NVMe)
- **Audio**: ALC1220 analog → alc1220-analog-sink (PipeWire 1.6.2)
- **Kernel**: 7.0-x86_64 Manjaro, preempt=full

## Input Devices
- **Mouse**: Corsair Katar Pro XT (USB 1b1c:1bac)
- **Keyboard/Headset**: BY Tech Thor 230 (USB 331a:5020)

## Verified Working Commands

### Check everything at once
```bash
cat /proc/cmdline | tr ' ' '\n'
kreadconfig5 --file kwinrc --group Compositing --key Enabled
cat /sys/module/usbhid/parameters/mousepoll
cat /sys/module/usbhid/parameters/quirks
udevadm info /dev/input/by-id/usb-Corsair_CORSAIR_KATAR_PRO_XT* 2>&1 | grep MOUSE_POLL
sudo libinput list-devices 2>&1 | grep -A 30 'Corsair.*Mouse' | grep Accel
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
grep HugePages_Total /proc/meminfo
sysctl kernel.sched_rt_runtime_us vm.swappiness vm.dirty_ratio vm.page-cluster
systemctl is-active power-profiles-daemon
nvidia-smi -q -d PERFORMANCE 2>&1 | grep 'Performance State'
```

### Fix mouse acceleration on KDE Wayland
```bash
rm -f /etc/libinput/local-overrides.quirks
sed -i '/\[Libinput\]\[6940\]\[7084\]\[Corsair/,/^$/d' ~/.config/kcminputrc
kwriteconfig5 --file kcminputrc --group Mouse --key "XLbInptAccelProfileFlat" "true" --type bool
kwriteconfig5 --file kcminputrc --group Mouse --key "AccelerationProfile" "0"
kquitapp5 kcminit; sleep 1; kstart5 kcminit
# Then replug mouse dongle
```

## Files Created During Session
- `/etc/default/grub` — full GRUB cmdline
- `/etc/udev/hwdb.d/71-corsair-polling.hwdb`
- `/etc/sysctl.d/99-workstation.conf`
- `/etc/environment.d/99-nvidia-wayland.conf`
- `/usr/lib/systemd/system-sleep/latency-fix`
- `~/.config/kwinrc` — Compositing section
- `~/.config/kcminputrc` — Mouse section

## What Broke & How It Was Fixed
| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Resume hook never ran | `case $2 in post)` should be `case "$1" in post)` | Fixed argument check |
| C-state fix errored every boot | `intel_idle/max_cstate` sysfs missing on kernel 7.0 | Removed from hook, use GRUB `processor.max_cstate=1` |
| `nvidia-smi -frl` failed | Flag doesn't exist on 595 driver | Removed, use `-pm 1` only |
| Hugepages 0 after boot | `nr_hugepages=` passed to userspace, not kernel | Changed to `hugepages=2048` |
| Hugepages 512 after sleep | Memory fragmentation | Added `compact_memory` + progressive alloc in hook |
| Mouse still felt smoothed | Invalid libinput quirk file + KDE per-device adaptive profile | Removed quirks file, cleared per-device override, set global flat |
