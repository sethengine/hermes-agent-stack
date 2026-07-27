# Hardware Voltage Sensor Investigation on Modern Linux Systems

## When to Use This Reference

Trigger when the user:
- Asks "are my voltages normal?" / "check Vcore/DRAM voltage"
- Reports that `sensors` shows no voltage readings (no `in0`, `Vcore`, `VIN#` entries)
- Has a modern Intel motherboard (Z890, Arrow Lake, LGA1851) or modern AMD board
- Wants to verify BIOS defaults for CPU/DRAM voltages are sane

## The Problem

Modern motherboards (Intel 700/800 series, AMD AM5) have moved hardware monitoring from the legacy LPC/ISA Super I/O chip to an **eSPI-connected embedded controller** or a **dedicated monitoring chip on SMBus**. Linux kernel drivers (`nct6775`, `it87`, `nct6683`) target ISA/LPC-attached chips and **will not load** on these platforms.

**Expected result of `sensors` on a Z890 board:** temperatures only (coretemp, spd5118 DIMM temps, gigabyte_wmi temps, NVMe). No voltages.

## Systematic Investigation Checklist

Run these in order to determine why voltages are missing and whether a workaround exists.

### Step 1: Identify the Board

```bash
cat /sys/devices/virtual/dmi/id/board_vendor
cat /sys/devices/virtual/dmi/id/board_name
cat /sys/devices/virtual/dmi/id/bios_version
```

### Step 2: Check `sensors` Output

Look for `in0`, `in1`, ... `Vcore`, `VIN#` entries. If sensors shows only temps (coretemp, spd5118, gigabyte_wmi, nvme), the voltage monitoring chip has no driver.

### Step 3: Check Available hwmon Devices

```bash
for hwmon in /sys/class/hwmon/hwmon*/; do
  n=$(cat ${hwmon}name 2>/dev/null)
  echo "=== $hwmon ($n) ==="
  ls ${hwmon} | grep -E "(in|volt|curr)" | head -5
done
```

No `in*` files = no voltage sensors exposed by any driver.

### Step 4: Try Available Kernel Drivers

```bash
# Standard Super I/O drivers (LPC/ISA)
sudo modprobe nct6775
sudo modprobe it87
sudo modprobe nct6683

# Check result
dmesg | tail -5
```

All three commonly return "No such device" on Z890/eSPI platforms.

### Step 5: Check for Traditional Super I/O Chip on LPC

```bash
# Probe standard Super I/O configuration ports
# Port 0x2E/0x2F for LPC, 0x4E/0x4F for some variants
sudo python3 -c "
import struct
with open('/dev/port', 'wb') as f:
    f.seek(0x2E)
    f.write(struct.pack('B', 0x20))  # Chip ID reg
with open('/dev/port', 'rb') as f:
    f.seek(0x2F)
    val = struct.unpack('B', f.read(1))[0]
    print(f'Chip ID: 0x{val:02x}')  # 0xFF = no chip
"
```

0xFF = no Super I/O chip at that port.

### Step 6: Probe SMBus for Hidden Monitoring Devices

```bash
i2cdetect -l           # Find SMBus adapter
sudo i2cdetect -y <N>  # Probe for devices
```

On Z890, the PCH SMBus controller is typically at `0000:80:1f.4` on i2c-11.

**Known devices found on Gigabyte Z890:**
| Address | Device | Notes |
|---------|--------|-------|
| 0x50-0x53 | SPD5118 (DDR5 DIMM) | Temp only, handled by kernel `spd5118` driver |
| 0x44 | Unknown monitoring chip | First read returns 0xff00 — could be the VRM controller or NCT chip |
| 0x48-0x4b | Unknown | Returns 0x0000 on probe |

### Step 7: Check ACPI EC Interface

```bash
ls /proc/acpi/ec/ 2>/dev/null
ls /sys/kernel/debug/ec/ 2>/dev/null
lsmod | grep ec_sys
```

If no EC interface is exposed, the Embedded Controller doesn't have a userspace ACPI binding.

### Step 8: Check MSR Voltage Registers (Intel)

```bash
sudo modprobe msr
sudo rdmsr -a 0x198  # IA32_PERF_STATUS — contains VID/frequency
```

Permission may be denied without root. The VID value can be decoded to voltage via the processor's specific voltage table.

### Step 9: Check WMI Interface (Gigabyte Boards)

Gigabyte Z890 boards expose multiple WMI GUIDs under the `DEADBEEF` prefix:

```bash
ls -d /sys/bus/wmi/devices/DEADBEEF-*/
```

| GUID | Object | Flags | Driver | Content |
|------|--------|-------|--------|---------|
| `DEADBEEF-2001` | BB | not expensive, not setable | `gigabyte-wmi` | **Temperature-only** via hwmon |
| `DEADBEEF-1000` | AA | **expensive=1, setable=1** | **No driver** | **Likely voltages + full sensor data** |
| `DEADBEEF-4002` | E2 | notify_id=0 | No driver | Event/notification device |

**The `DEADBEEF-1000` device (object AA)** is flagged "expensive" (takes time to query) and "setable" (can write to it). This is the interface that should return full hardware monitoring data including voltages. No kernel driver currently binds to it.

A kernel patch could add support by:
1. Writing WMI query method with the object_id "AA"
2. Decoding the returned data block into voltage/current/power readings
3. Exposing them as standard hwmon `in*` inputs

### Step 10: Check CPU Frequency + Power Info (Non-Voltage Proxy)

Even without direct voltage readings, you can verify the CPU power state:

```bash
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver  # intel_pstate expected
```

## Normal Voltage Ranges (for Reference)

### Intel Core Ultra 7 265K (Arrow Lake, Z890)

| Rail | Idle | Load (Stock) | Notes |
|------|------|-------------|-------|
| **CPU Vcore** | 0.65-0.95V | 1.15-1.35V | Arrow Lake stock VID typically 1.2-1.3V max |
| **VCCSA** (System Agent) | 0.85-1.05V | 0.95-1.10V | Auto usually ~0.95V |
| **VCCIO** | 0.85-1.00V | 0.90-1.05V | Auto usually ~0.92V |

### DDR5 on Z890

| Rail | JEDEC | XMP/EXPO | Notes |
|------|-------|----------|-------|
| **VDD** | **1.10V** | 1.25-1.45V | Primary DRAM voltage |
| **VDDQ** | **1.10V** | 1.25-1.40V | Usually matches VDD |
| **VPP** | **1.80V** | 1.80V | Always 1.8V for DDR5 |

### PSU Rails (ATX Spec ±5%)

| Rail | Min | Max |
|------|-----|-----|
| +12V | 11.4V | 12.6V |
| +5V | 4.75V | 5.25V |
| +3.3V | 3.14V | 3.47V |

## Fallback: Check in BIOS

Since Linux can't read voltages on these modern boards without a kernel driver, the fastest check is:

1. Reboot → **Del** key → Gigabyte BIOS
2. Navigate to **Tweaker** page → **Advanced Voltage Settings** (or **PC Health Status**)
3. Read Vcore, DRAM VDD/VDDQ, VPP, +12V, +5V, +3.3V directly

## If You Need a Permanent Fix

Options ordered by effort:

1. **Build kernel module** — Patch the `nct6775` driver to support the new eSPI-based chip, or write a driver for the `DEADBEEF-1000` WMI interface
2. **Use `i2c-dev` userspace** — With root access, write a Python script to poll the SMBus monitoring chip directly (probe 0x44 on SMBus)
3. **Dual-boot or live USB** — Boot a Windows PE or Linux distro with the vendor's monitoring tools
4. **External hardware monitor** — Cheap USB voltage/current monitor (works regardless of OS)

## Key Takeaway

**Modern motherboard voltage monitoring is completely inaccessible from Linux without the right kernel driver.** This is not a misconfiguration — it's a missing driver for the eSPI-connected monitoring chip (Nuvoton NCT series or ITE IT series on new bus interface). The `DEADBEEF-1000` WMI device on Gigabyte boards is the most promising path for a software fix.
