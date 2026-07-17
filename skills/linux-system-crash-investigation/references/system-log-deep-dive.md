# System Log Deep Dive — Journalctl Forensic Investigation

A systematic methodology for investigating system health, failed boots, reboots, and errors using journalctl and related tools. Covers the full pipeline from boot history analysis to individual error investigations.

## Quick-Start — The 5-Command Sweep

```bash
# 1. Boot history with uptimes
journalctl --list-boots

# 2. All errors in current boot
journalctl -p err -b --no-pager | tail -80

# 3. Critical errors
journalctl -p crit -b --no-pager | tail -40

# 4. Failed systemd units
systemctl --failed

# 5. Kernel errors in current boot
dmesg -l err,crit,alert,emerg 2>/dev/null || journalctl -b -k --priority=err --no-pager
```

## Noise Filtering — Seeing the Real Errors

Many boot-time errors are known-harmless noise. Filter them out to reveal actionable errors:

```bash
# Common noise patterns to filter (adjust for each system)
journalctl -b -p err --no-pager | grep -v \
  -e 'Could not chase sysfs attribute' \
  -e 'Failed to write file' \
  -e 'conversation failed' \
  -e 'incorrect password' \
  -e 'password is required' \
  -e 'Activation request for' \
  -e 'Applying output configuration failed' \
  -e 'watchdog did not stop'
```

**Know your local noise:** most systems have 2-5 repeat patterns that appear every boot. Systematically filter them after the first investigation so future checks see only new/interesting errors. Common per-system noise: stale udev rules referencing removed sysfs paths, NVIDIA power state transitions, ACPI firmware quirks, Bluetooth init failures, `systemd-tmpfiles` CPU governor write failures (already set by GRUB).

## Step-by-Step Investigation

### 1. Boot History Analysis

```bash
# List all boots with first/last entry timestamps
journalctl --list-boots

# Identify BOOT CHAINS (rapid reboots) by uptime:
# Multiple boots within minutes of each other = crash loop
journalctl --list-boots --no-pager 2>&1 | awk '{
  split($NF, end, " ");
  split($(NF-1), start, " ");
  if (start[1] == end[1] && start[2] == end[2]) {
    split(start[4], st, ":");
    split(end[4], en, ":");
    diff = (en[1]*3600+en[2]*60+en[3]) - (st[1]*3600+st[2]*60+st[3])
  } else { diff = 99999 }
  if (diff < 600 && $1 != 0) print $0, "SHORT=" diff "s"
}'

# Example chain output:
#   -4 06-13 23:33:46 EEST Sat 06-13 23:34:37 EEST  SHORT=51s  <- CRASH
#   -3 06-13 23:35:43 EEST Sat 06-13 23:36:41 EEST  SHORT=58s  <- CRASH AGAIN
#   -2 06-13 23:37:47 EEST Sat 06-13 23:38:26 EEST  SHORT=39s  <- CRASH LOOP
# This is a crash loop — the system isn't surviving long enough

# For a quick visual scan of all boot timestamps (compact):
journalctl --list-boots --no-pager 2>&1 | awk '{print $1, $4, $5, $6, $7, $8}'
```

### 2. Cross-Boot Error Sweep

```bash
# Check each of the last N boots for scx/scheduler crashes
for b in 0 1 2 3 4 5; do
  c=$(journalctl -b -$b --no-pager --no-hostname 2>&1 | grep -c 'scx_rustland.*ABRT\|kwin_wayland.*dumped core' 2>/dev/null)
  [ "$c" -gt 0 ] && echo "Boot -$b: $c crashes"
done

# Priority-level triage — err, crit, alert, emerg in parallel
journalctl -p err -b --no-pager | tail -80
journalctl -p crit -b --no-pager | tail -40
journalctl -p alert -b --no-pager | tail -20

# Count specific error types in current boot
journalctl -b --no-pager --no-hostname 2>&1 | grep 'dumped core' | awk '{print $3}' | sort | uniq -c | sort -rn

# Check for errors that appear EVERY boot (systematic issues)
# Common systematic errors on this system:
journalctl -b --no-pager --no-hostname 2>&1 | grep -c 'Activation request for.*failed'
journalctl -b --no-pager --no-hostname 2>&1 | grep -c 'watchdog did not stop'
journalctl -b --no-pager --no-hostname 2>&1 | grep -c 'Could not chase sysfs attribute'
```

### 3. Suspend/Resume Analysis

```bash
# Find all suspend/resume cycles in current boot
journalctl -b --no-pager --no-hostname 2>&1 | grep -E 'PM: suspend|PM: resume|suspend exit|suspend entry'

# Check what happened between resume and crash
journalctl -b -1 --no-pager --no-hostname 2>&1 | sed -n '/PM: suspend exit/,/watchdog did not stop/p'

# Check NVIDIA suspend/resume service status
systemctl status nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service

# Check if NVIDIA license override is in place
cat /etc/systemd/system/nvidia-suspend.service.d/override.conf 2>/dev/null

# Check DMAR faults during resume
journalctl -b --no-pager --no-hostname 2>&1 | grep 'DMAR.*INTR-REMAP\|DMAR.*fault'
```

### 4. Systemd Unit Failures

```bash
# Show ALL failed units
systemctl --failed

# Detailed view of a failed unit
systemctl status <unit-name> --no-pager

# Find what caused the failure
journalctl -u <unit-name> --no-pager

# Check if the referenced paths exist
ls -la /sys/bus/usb/devices/<referenced-device>/ 2>&1
ls -la <any-path-in-error-message> 2>&1
```

### 5. Hardware Error Investigation

```bash
# Check BERT (Boot Error Record Table)
journalctl -b -k --no-pager | grep -i 'BERT'

# Check if it's persistent across boots
for b in 0 1 2 3 4 5; do echo "Boot -$b:"; journalctl -b -$b -k --no-pager 2>&1 | grep -c 'BERT'; done

# Raw BERT data
sudo cat /sys/firmware/acpi/tables/data/BERT | xxd | head -30

# Memory errors
journalctl -b --no-pager --no-hostname 2>&1 | grep -i 'EDAC\|ECC\|mce\|Machine Check\|hardware error'

# PCIe errors
journalctl -b --no-pager --no-hostname 2>&1 | grep -i 'PCIe.*error\|AER.*error\|correctable error'

# OOM (Out Of Memory) killer events
journalctl -b -p err --no-pager | grep -i 'oom\|out of memory\|killed process\|memory pressure'

# IGC network adapter PTM timeout (common on Intel I225/I226 2.5GbE on modern boards)
journalctl -b --no-pager --no-hostname 2>&1 | grep 'Timeout reading IGC_PTM_STAT register'
# Note: usually harmless on resume — the adapter reinitializes. Only actionable if networking
# is actually broken after the timeout.
```

### 6. USB Device Topology Investigation

```bash
# List USB tree
lsusb -t
ls /sys/bus/usb/devices/

# Identify specific devices
udevadm info /sys/bus/usb/devices/3-5 2>&1 | grep -E 'ID_VENDOR|ID_MODEL|ID_SERIAL|DEVTYPE|DRIVER'

# Check wakeup status of ALL USB devices
for dev in /sys/bus/usb/devices/*/power/wakeup; do
  path=$(dirname "$dev")
  name=$(udevadm info -q property "$path" 2>/dev/null | grep -E 'ID_MODEL=' | head -1)
  val=$(cat "$dev" 2>/dev/null)
  echo "$(basename $path): wakeup=$val  $name"
done

# Verify udev rules are hitting the right targets
udevadm test $(udevadm info -q path /sys/bus/usb/devices/3-5) 2>&1 | grep -E 'power|autosuspend|wakeup'
```

## Common Patterns & Their Root Causes

| Pattern | Likely Cause | Diagnosis |
|---------|-------------|-----------|
| scx_rustland ABRT after resume | hwloc topology inconsistency on Intel hybrid CPU | Check `journalctl | grep 'intersection without inclusion'` |
| `Atomic modeset test failed! Permission denied` | NVIDIA + KWin display conflict at resume | Check `journalctl | grep 'Atomic modeset'` |
| `DMAR [INTR-REMAP] fault reason 0x22` | Stale IRTE entries after resume (NVIDIA audio) | Check `journalctl | grep 'DMAR.*INTR-REMAP'` |
| `watchdog: watchdog0 did not stop!` at shutdown | iTCO_wdt driver doesn't stop watchdog on shutdown | Usually harmless, every boot |
| `Could not chase sysfs attribute` during udev | udev rule targets a path/attribute that doesn't exist | Verify the rule's ATTR path exists |
| Rapid reboot chain (multiple boots <2min) | Crash during early boot — kernel panic, GPU hang, or driver init failure | Check first boot in chain for the original failure |
| `Failed to start <service>` | Service script references stale paths or missing devices | `systemctl status <service>` shows exact error |
