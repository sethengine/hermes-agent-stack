---
name: linux-hardware-monitoring
description: "Read motherboard sensors (voltages, temperatures, fans) on Linux — identify monitoring chips, load kernel drivers, handle WMI-based monitoring on Gigabyte/HP boards, and troubleshoot missing sensors."
category: devops
triggers:
  - "check voltages"
  - "read sensors"
  - "hardware monitoring"
  - "motherboard sensors"
  - "lm-sensors"
  - "missing sensors in Linux"
  - "gigabyte sensor driver"
---

# Linux Hardware Monitoring

## Overview

Read motherboard hardware sensors (CPU Vcore, DRAM voltage, +12V/+5V/+3.3V rails, temperatures, fan speeds) on Linux. Covers both traditional Super I/O chips and modern WMI/embedded-controller-based monitoring.

## Detection Flow

### 1. Check what lm-sensors already sees

```bash
sensors                         # all sensors
sensors -u -A                   # raw values, no formatting
for d in /sys/class/hwmon/hwmon*/; do
    n=$(cat ${d}name)
    echo "=== $d ($n) ==="
    ls ${d} | grep -E "(in|volt|curr|temp|fan|power)"
done
```

Missing `in0`, `in1`, etc. entries under hwmon means the voltage monitoring chip has no driver loaded.

### 2. Identify the monitoring chip

Check what kernel modules exist for monitoring:

```bash
# Available Super I/O / EC-based drivers
ls /lib/modules/$(uname -r)/kernel/drivers/hwmon/  # it87, nct6775, nct6683, etc.

# Platform-specific WMI drivers
ls /lib/modules/$(uname -r)/kernel/drivers/platform/x86/ | grep -E "(gigabyte|hp|asus|acer)"
```

Check which chips are responsive on the LPC/ISA Super I/O ports:

```bash
# Traditional ISA/LPC Super I/O detection
sudo modprobe it87 ignore_resource_conflict=1
sudo modprobe nct6775
sudo modprobe nct6683
```

If those return "No such device", the chip uses eSPI (modern platforms) or an embedded controller.

### 3. SMBus probe for hidden chips

```bash
# Find SMBus adapter (usually i2c-N where N is the PCH SMBus)
i2cdetect -l
# Probe for chips (0x44-0x4F are common for ITE/Nuvoton)
sudo i2cdetect -y <bus_number>
# Check if a detected chip is a known ITE/Nuvoton
sudo i2cget -y <bus> <addr> 0x00 w
# Returns like 0xff00 or 0x8622 which is the chip ID
```

### 4. Modern Gigabyte boards (Z790/Z890, X670/X870)

Gigabyte Z890 boards use an **iTE I/O Controller Chip** (IT8689E, IT8792E, etc.) for all hardware monitoring. The Linux `gigabyte-wmi` driver (`gigabyte_wmi` module) only exposes 6 temperatures — **not** voltages.

To get full voltage readings:

```bash
sudo modprobe it87 ignore_resource_conflict=1 force_id=0x8689
```

This typically exposes `in0`-`in9` for voltages (Vcore, +12V, +5V, +3.3V, DRAM VDD/VDDQ, etc.) plus fan and temp sensors.

If the standard Super I/O port (0x2E/0x4E) returns 0xFF, the chip is connected via **eSPI** and may not be accessible without the right driver or kernel support.

#### Gigabyte WMI Interface Reference

The WMI device at GUID `DEADBEEF-2001-0000-00A0-C90629100000` (object `BB`) provides method-based access via `wmidev_evaluate_method()`. The command IDs include:

| Command | Name | Description |
|---------|------|-------------|
| 0x125 (293) | `ZFCGetCurrentTemp` | Temperature query (sensor # in arg1) |
| **0x118 (280)** | **`EZVGetVoltage`** | **Voltage query** (not exposed by current driver) |
| 0x119 (281) | `EZVSetVoltage` | Set voltage |
| 0x11A (282) | `EZVGetHwId` | Get voltage rail HW ID |
| 0x120 (288) | `EZVGetItem` | Get voltage UI item |

See `references/gigabyte-wmi-methods.md` for the full decompiled WMI method table.

### 5. HP business desktops

Use the `hp-wmi-sensors` driver (separate from `hp-wmi`):

```bash
sudo modprobe hp-wmi-sensors
```

This driver exposes voltages, temps, and fans through the standard hwmon interface.

### 6. ASUS boards

```bash
sudo modprobe asus-wmi-sensors
```

## Working Without Root

If `sudo` is unavailable, you are limited to:

- `sensors` output (already-loaded drivers only)
- `hwmon` sysfs inspection
- `dmidecode` from sysfs (`/sys/devices/virtual/dmi/id/`)
- Checking `/proc/cpuinfo`, `/sys/devices/system/cpu/cpufreq/`
- Reading ACPI tables from `/sys/firmware/acpi/tables/` (root-only on modern kernels)
- SMBus /dev/i2c access (typically root-only)

You cannot:
- Load kernel modules
- Call ACPI methods
- Use i2cget/i2cdetect
- Read MSRs
- Access /dev/mem or /dev/port

## Pitfalls

- **Kernel module signing**: Modern distros (Manjaro, Ubuntu with Secure Boot) require signed modules. Loading a self-built `it87` module will fail with "Required key not available". Use the distro-provided module.
- **No such device**: Means the chip isn't at the expected LPC/ISA address. Try `force_id` or check SMBus.
- **eSPI vs LPC**: Super I/O ports 0x2E/0x4E return 0xFF on eSPI-connected chips. The `it87` driver may still work if the kernel has eSPI support compiled in.
- **ACPI resource conflicts**: `ignore_resource_conflict=1` on `it87` — the ACPI firmware claims the I/O ports. This is usually safe but can theoretically cause a race.
- **SPD5118 DIMM temps**: DDR5 DIMMs have integrated thermal sensors. The kernel's `spd5118` driver exposes these as `spd5118-i2c-*` hwmon entries — these are DIMM temperatures, not motherboard voltages.
- **WMI data block vs method**: GUID `DEADBEEF-1000` (object AA, expensive flag) is a data block, NOT a callable method. GUID `DEADBEEF-2001` (object BB, method flag) is the method interface.

## Verify

After loading `it87`:

```bash
sensors | grep -E "(Vcore|VIN|in[0-9]|+12V|+5V|+3.3V)"
cat /sys/class/hwmon/hwmon*/name | grep it87
# Check for voltage entries
find /sys/class/hwmon/ -name "in*_input"
```
