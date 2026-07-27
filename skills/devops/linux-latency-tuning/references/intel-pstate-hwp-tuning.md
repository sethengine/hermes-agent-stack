# intel_pstate HWP Tuning on Kernel 7.0+ (Arrow Lake / Ultra 200 Series)

## The Problem: energy_performance_preference Is Read-Only

On kernel 7.0+ with `intel_pstate=active` (HWP mode) on modern Intel (Arrow Lake / Ultra 7 265K and newer), the per-CPU `energy_performance_preference` sysfs at `/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference` is **read-only**. Writing `performance` produces `Device or resource busy`:

```
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
# -bash: echo: write error: Device or resource busy
```

This is NOT a bug — it is expected kernel behavior. When `intel_pstate` runs in `active` mode, it uses the HWP (Hardware P-State) interface built into the CPU. The EPP (Energy Performance Preference) is a HWP hardware register managed by the CPU microcode. The kernel's intel_pstate driver exposes the sysfs as a status indicator but the hardware firmware owns the actual register.

## Detection

```bash
# Check intel_pstate mode
cat /sys/devices/system/cpu/intel_pstate/status
# → "active" means HWP mode (EPP is read-only)
# → "passive" means legacy ACPI mode (EPP is writable)

# Check current EPP value
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
# → "default" means under HWP firmware control

# Check available preferences
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_available_preferences
# → default performance balance_performance balance_power power
```

## The Correct Tuning Approach

When EPP is locked by HWP, tune via intel_pstate's global parameters instead:

### min_perf_pct (Most Impactful)

Controls the minimum allowed CPU frequency as a percentage of the max range. The hardware won't drop below this floor.

```bash
# Check current
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct
# → Default is typically 25 (allows CPU to drop to 800 MHz on Ultra 7 265K)

# Set higher floor — reduces frequency transition latency
echo 70 | sudo tee /sys/devices/system/cpu/intel_pstate/min_perf_pct
# → Hardware now stays at >=70% of max frequency
# → scaling_cur_freq shows higher idle values (1.8-4.6 GHz vs 800 MHz)

# Verify
cat /sys/devices/system/cpu/intel_pstate/min_perf_pct
grep . /sys/devices/system/cpu/cpu[0-3]/cpufreq/scaling_cur_freq
```

Values:
| min_perf_pct | Behavior | Use Case |
|---|---|---|
| 25 (default) | CPU can drop to 800 MHz | Power saving, battery |
| 50 | Moderate floor, ~2-2.7 GHz idle | Balanced |
| 70-80 | High floor, ~3-4 GHz idle | Latency-sensitive desktop |
| 100 | Always at max turbo | Maximum responsiveness, high power |

### max_perf_pct

Controls the maximum allowed frequency. Usually left at 100.

```bash
cat /sys/devices/system/cpu/intel_pstate/max_perf_pct
# → 100 (default, correct for desktop)
```

### hwp_dynamic_boost — Must Verify After Any Tuning

`hwp_dynamic_boost=1` allows the HWP hardware to dynamically boost frequency in response to task activity. **This flag can be inadvertently cleared when writing to other intel_pstate sysfs entries** (e.g., testing EPP writes via `echo performance > ...` from a shell loop across all CPUs).

```bash
# Check
cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost
# → 1 = enabled (correct for desktop)
# → 0 = disabled (restore immediately)

# Restore
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost
```

**Always verify `hwp_dynamic_boost` after any intel_pstate tuning session.** It is easy to clear and you won't notice until responsiveness degrades.

### Static Frequency (Alternative to min_perf_pct)

If you want to lock frequency entirely rather than set a floor:

```bash
# Lock to max frequency (bypasses HWP scaling)
cpupower frequency-set -g performance -u 5.4GHz -d 5.4GHz

# Lock to a specific frequency
cpupower frequency-set -g performance -u 4.5GHz -d 4.5GHz
```

## The Full Verified State

After tuning for desktop latency, verify all of these match:

```bash
echo "min_perf_pct:     $(cat /sys/devices/system/cpu/intel_pstate/min_perf_pct)"
echo "max_perf_pct:     $(cat /sys/devices/system/cpu/intel_pstate/max_perf_pct)"
echo "hwp_dynamic_boost: $(cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost)"
echo "epp:              $(cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference)"
echo "governor:         $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "driver:           $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver)"
```

Expected for latency-tuned HWP desktop:
- `min_perf_pct: 70` (or higher floor)
- `max_perf_pct: 100`
- `hwp_dynamic_boost: 1`
- `epp: default` (HWP-managed, expected on active mode)
- `governor: performance`
- `driver: intel_pstate`

## Persistence

### Via systemd service

```ini
[Unit]
Description=CPU Performance Tuning for Desktop Latency
After=sysinit.target
Before=display-manager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c 'echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct'
ExecStart=/bin/sh -c 'echo 100 > /sys/devices/system/cpu/intel_pstate/max_perf_pct'
ExecStart=/bin/sh -c '[ "$(cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost)" != "1" ] && echo 1 > /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost || true'

[Install]
WantedBy=multi-user.target
```

### Via resume hook

Add to `/usr/lib/systemd/system-sleep/latency-fix`:

```bash
case "$1" in
    post)
        echo 70 > /sys/devices/system/cpu/intel_pstate/min_perf_pct
        [ "$(cat /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost)" != "1" ] && \
            echo 1 > /sys/devices/system/cpu/intel_pstate/hwp_dynamic_boost || true
        ;;
esac
```

## System Profile Verified With This Approach

- CPU: Intel Ultra 7 265K (Arrow Lake, 20 cores: 8P+12E)
- Motherboard: Gigabyte Z890 AERO G
- GPU: NVIDIA RTX 5060 Ti (GB206, driver 595.71.05)
- Kernel: 7.0.10-1-MANJARO
- KDE Plasma: 6.6.5 (Wayland)
- GRUB params: `preempt=full threadirqs intel_idle.max_cstate=1 processor.max_cstate=1 skew_tick=1 ...`

Tested: `min_perf_pct` values 25 → 70 → 90. At 70, cores idle at 1.8-4.6 GHz. At 90, idle at 4.3-5.1 GHz. 70 was chosen as the best trade-off.
