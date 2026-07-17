---
name: linux-system-crash-investigation
description: >
  Systematic investigation of unexplained system crashes and reboots on Linux.
  Covers journalctl boot analysis, GPU/driver fault hunting (NVIDIA Xid, AMD GPU),
  IRQ affinity debugging, kernel parameter forensics, and hardware watchdog checks.
  Use when user reports system restarting/crashing unexpectedly.
---

## Linux System Crash & Reboot Investigation

### Phase 1: Boot History & Crash Signature

```bash
# Get full boot timeline
journalctl --list-boots

# Check last boot for clean shutdown
journalctl -b -1 --no-pager | grep -E 'systemd-shutdown|Journal stopped|SIGTERM'

# Absence = hard crash (no clean shutdown logged)

# Check for kernel panic/oops in any recent boot
journalctl -b -1 -k --no-pager | grep -iE 'panic|oops|Call Trace|BUG|lockup|hung_task|rcu.*stall'

# Check for segfaults/coredumps in userspace
journalctl -b -1 --no-pager | grep -iE 'segfault|SIGSEGV|dumped core|oom.kill'
```

### Phase 2: GPU Fault Hunting (NVIDIA)

```bash
# Xid errors = GPU hardware faults
journalctl -b -1 -k --no-pager | grep 'NVRM: Xid'
# Also check current boot and older boots
journalctl -b 0 -k | grep Xid
journalctl -b -2 -k --no-pager | grep Xid

# Decode Xid codes - see references/nvidia-xid-codes.md
# Common patterns:
#   Xid 31: MMU Fault - GPU page table fault, often NVDEC0 (video decoder)
#   Xid 79: GPU has fallen off the bus (PCIe issues)
#   Xid 45: Preemptive channel removal
```

### Phase 3: IRQ Affinity & CPU Isolation Interaction

```bash
# Check which CPUs are isolated vs housekeeping
cat /proc/cmdline | tr ' ' '\n' | grep -E 'isolcpus|nohz_full|rcu_nocbs'
cat /sys/devices/system/cpu/nohz_full
cat /sys/devices/system/cpu/isolated

# Full IRQ-to-CPU mapping with classification
# Uses scripts/check_irq_affinity.py — classifies by isolated/housekeeping
python3 scripts/check_irq_affinity.py

# Key check: are GPU/USB/NVMe IRQs landing on housekeeping cores
# or isolated cores? The GPU IRQ handler needs timer ticks enabled.
```

### Phase 4: Kernel Parameter Forensics

```bash
# Compare cmdline across recent boots
journalctl -b -1 -k --no-pager | grep 'Command line'
journalctl -b -2 -k --no-pager | grep 'Command line'
cat /proc/cmdline  # current boot

# Key parameters that affect stability:
#   pcie_aspm=off/pcie_aspm.policy=performance  -- aggressive PCIe
#   pci=pcie_bus_perf,pcie_ports=native         -- native PCIe handling
#   intel_iommu=on                              -- GPU DMA through IOMMU
#   iommu=pt                                    -- IOMMU passthrough mode
#   nvidia_drm.modeset=1,nvidia_drm.fbdev=1    -- NVIDIA kernel modesetting
```

### Phase 5: Watchdog Configuration

```bash
# Hardware watchdog
ls -la /dev/watchdog*
dmesg | grep -iE 'watchdog|iTCO|wdt'

# Kernel watchdog
cat /proc/sys/kernel/nmi_watchdog
cat /proc/sys/kernel/softlockup_panic
cat /proc/sys/kernel/hardlockup_panic

# Systemd watchdog
grep -r 'RuntimeWatchdogSec\|WatchdogSec' /etc/systemd/

# If iTCO_wdt is blacklisted, no hardware watchdog → hung system stays hung
```

### Phase 6: Frame the Crash Timeline

Reconstruct the exact sequence:
1. When was the last normal log entry before silence?
2. What was the last process running? Steam? Chrome? pamac?
3. What GPU errors preceded the crash (if any)?
4. Was there an intervening event (scxctl, sudo, service start)?
5. What changed in the kernel cmdline between the crash boot and the next boot?

### Phase 7: sched_ext / scx_rustland Crash Investigation

```bash
# Check if scx scheduler is active
cat /sys/kernel/sched_ext/root/ops
ps aux | grep scx_

# Check for scheduler crashes
journalctl -b --no-pager | grep -iE 'scx_rustland.*ABRT|scx.*signal|scx.*coredump|scx_watchdog'

# Check for hwloc topology errors (root cause of scx_rustland SIGABRT after resume)
journalctl -b --no-pager | grep -i 'hwloc.*invalid\|hwloc.*intersection\|intersection without inclusion'

# Verify CPU cluster topology consistency
cat /sys/devices/system/cpu/cpu*/topology/cluster_cpus_list 2>/dev/null | sort -u
cat /sys/devices/system/cpu/cpu*/topology/cluster_id 2>/dev/null | sort -u
cat /sys/devices/system/cpu/cpu0/cache/index3/shared_cpu_list
```

### Phase 8: BERT (Boot Error Record Table) Investigation

```bash
# Check if BERT error exists
journalctl -b -k --no-paper | grep -i 'BERT'

# Check in all recent boots
for b in 0 1 2 3 4 5; do echo "Boot -$b:"; journalctl -b -$b -k --no-paper 2>&1 | grep -c 'BERT'; done

# Raw BERT data (root-only)
sudo cat /sys/firmware/acpi/tables/data/BERT | xxd | head -30

# Size check — 0 bytes = no error, >0 = real CPER record
sudo wc -c /sys/firmware/acpi/tables/data/BERT

# Install rasdaemon for proper CPER decoding
sudo pacman -S rasdaemon
sudo systemctl enable --now rasdaemon
ras-mc-ctl --errors

# Verify APEI is compiled in
zgrep 'CONFIG_ACPI_APEI' /proc/config.gz 2>/dev/null || grep 'CONFIG_ACPI_APEI' /boot/config-*
```

**BERT "Skipped" meaning:** The kernel's APEI driver found a CPER (Common Platform Error Record) in the BERT table but couldn't decode it. This is often a firmware bug where the BIOS writes records in a format the kernel doesn't understand. Common on Gigabyte/ASUS AMI BIOS boards. Usually harmless.

### Phase 9: DMAR/IOMMU Fault Investigation (NVIDIA GPU Audio)

DMAR fault storms from the NVIDIA GPU's HDMI audio function (`02:00.1`) can cause a **full system crash cascade** — not just resume failures. This is a distinct crash mechanism from GPU compute/driver Xid errors.

```bash
# Check for interrupt remapping faults (any context — not just resume)
journalctl -b --no-pager | grep -i 'DMAR.*INTR-REMAP\\|DMAR.*fault\\|fault reason'

# Count fault occurrences in current boot
journalctl -b --no-pager | grep -c 'DMAR.*INTR-REMAP.*02:00'
```

**Fault signature:** `DMAR: [INTR-REMAP] Request device [02:00.1] fault index 0x... [fault reason 0x22] Present field in the IRTE entry is clear`

**Device:** `02:00.1` = NVIDIA GB206 High Definition Audio Controller (HDMI audio function on the GPU)

**Root cause:** The IOMMU's interrupt remapping table entry for the GPU's audio function goes invalid/missing. The `0x22` reason = "Present field in the IRTE entry is clear" — the interrupt redirection table entry has its present bit cleared, meaning the entry isn't valid. This can happen:
- During suspend/resume (stale IRQ state not restored after PCIe power state transition)
- During normal operation (IOMMU table corruption triggered by PCIe ATS interactions)

**Failure cascade when fault escalates to full system crash:**

```text
DMAR faults (02:00.1 GPU audio, hundreds) → GPU driver instability
  → nvidia_drm sync FD error
    → PipeWire loses connection → easyeffects coredump
      → All KDE Qt6 apps crash: "no Qt platform plugin could be initialized"
        → plasmashell killed with SIGKILL after systemd timeout
          → System journals corrupted, EFI dirty bit = unclean shutdown
          → kwinrc corrupted (was being written during crash) → KDE compositing/animations disabled on next boot
```

**Post-crash symptoms:**
- KDE compositing and animations disabled (kwinrc `Enabled=false`)
- `AnimationSpeed=0` in kwinrc
- `kconf_update` auto-migrated corrupted configs to defaults on next boot
- systemd-journald reports `corrupted or uncleanly shut down` for journals
- EFI partition shows `Dirty bit is set`

**Additional contributory signal:** ACPI BIOS error `\\RPTS.DTFS` (suspend/resume ACPI method) — motherboard firmware bug that can contribute to IOMMU instability.

**Fixes (in order of preference):**

1. **`pci=noats` (disable PCIe ATS)** — Most targeted fix. Disables PCIe Address Translation Services, eliminating the ATS-related IOMMU table interaction that corrupts interrupt remapping entries:
   ```bash
   sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="pci=noats /' /etc/default/grub
   sudo grub-mkconfig -o /boot/grub/grub.cfg
   sudo reboot
   ```

2. **`iommu.passthrough=1`** — Bypass IOMMU entirely for all devices (broader impact, less targeted):
   ```bash
   # Add to GRUB_CMDLINE_LINUX_DEFAULT instead of pci=noats
   iommu.passthrough=1
   ```

3. **Blacklist HDMI audio** — If HDMI audio isn't needed, prevent the driver from binding to the faulting device:
   ```bash
   echo 'options snd-hda-intel enable=0,1' | sudo tee /etc/modprobe.d/alsa-fix.conf
   sudo mkinitcpio -P  # if using initramfs
   ```

**Restore KDE settings post-crash:**
```bash
# Re-enable compositing
kwriteconfig6 --file kwinrc --group Compositing --key Enabled true
kwriteconfig6 --file kwinrc --group Compositing --key AnimationSpeed 200
kwriteconfig6 --file kwinrc --group Compositing --key Backend OpenGL
qdbus6 org.kde.KWin /Compositor resume

# Re-enable general KDE animations
kwriteconfig6 --file kdeglobals --group KDE --key AnimationDurationFactor 1
kwriteconfig6 --file kdeglobals --group KDE --key WidgetAnimationsEnabled true

# Apply
kquitapp6 plasmashell && sleep 1 && kstart6 plasmashell &
```

## Common Root Causes Found on This System

1. **libva-nvidia-driver + Chrome VA-API → NVDEC Xid 31**
   - Chrome uses `VaapiOnNvidiaGPUs`, `VaapiIgnoreDriverChecks`
   - Triggers NVDEC0 MMU faults
   - Fix: disable Chrome GPU video decode or remove `VaapiIgnoreDriverChecks`

2. **isolcpus on P-cores forcing Chrome onto E-cores**
   - Creates contention between GPU IRQs and Chrome on same slow cores
   - Makes post-fault recovery harder

3. **iTCO_wdt blacklisted → no auto-reboot on hang**
   - `modprobe.blacklist=iTCO_wdt` removes hardware watchdog
   - Hung GPU = system stays dead until manual reset

4. **scx_rustland + Intel hybrid CPU + resume: hwloc topology crash**
   - After resume from suspend, Intel Arrow Lake CPU cluster/L1d topology in sysfs becomes inconsistent
   - Specifically: `Group0 (P#24 cpuset 0x00000f00) at L1d (P#24 cpuset 0x00000110)` — two topology views of the same CPU overlap but don't nest
   - hwloc can't handle this → scx_rustland SIGABRT on re-initialization
   - Triggered by: resume from suspend, display hotplug/disconnect events that re-trigger scheduler re-init
   - Also produces secondary symptoms: `Atomic modeset test failed! Permission denied` in kwin
   - **Fix options:**
     a. Update scx_rustland to a version with better hwloc error handling
     b. Switch scheduler: `scx_lavd`, `scx_bpfland`, or `scx_loader --select <name>`
     c. Blacklist scx_rustland and use the kernel CFS on resume-sensitive workloads

5. **NVIDIA 595+ driver license change breaks suspend/resume `ExecCondition`**
   - NVIDIA driver module license changed from `"NVIDIA"` to `"Dual MIT/GPL"` starting with driver 595.x
   - The stock `nvidia-suspend.service` checks: `modinfo -F license nvidia | grep -q 'NVIDIA'` → **fails**
   - Result: NVIDIA suspend/resume hooks never execute
   - **Fix**: Override ExecCondition in `/etc/systemd/system/nvidia-{suspend,resume,hibernate}.service.d/override.conf`:
     ```
     [Service]
     ExecCondition=
     ExecCondition=/bin/sh -c "/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'"
     ```

6. **DMAR [INTR-REMAP] fault reason 0x22 — NVIDIA HDMI audio crash cascade**
   - Device [02:00.1] (NVIDIA HDMI audio) has stale IRTE entries
   - Can occur during normal operation (PCIe ATS interactions) not just resume
   - `Present field in the IRTE entry is clear` — IOMMU interrupt table corruption
   - Escalation: DMAR fault storm → GPU driver instability → PipeWire crash → KDE desktop crash → kwinrc corruption
   - **Fix**: `pci=noats` in GRUB_CMDLINE_LINUX_DEFAULT disables PCIe ATS
   - Alternatives: `iommu.passthrough=1` or blacklist HDMI audio module

## Pitfalls

- **Don't execute fixes without explaining first.** User wants to understand before changes are made.
- `isolcpus=managed_irq` allows managed IRQs (NVMe MSI-X) to target isolated CPUs — usually undesirable.
- `nohz_full` on the SAME cores as GPU IRQs would delay interrupt handling, but GPU IRQs usually go to separate (E-core) CPUs.
- `preempt=voluntary` prevents kernel from preempting hung GPU threads — `preempt=full` allows breaking deadlocks.
- **udev rules and USB power attributes:** `SUBSYSTEM=="usb"` matches both `usb_device` and `usb_interface` udev events. `power/autosuspend` and `power/wakeup` only exist at the USB device level, not on interfaces. Always add `DEVTYPE=="usb_device"` when setting power attributes:
  ```udev
  SUBSYSTEM=="usb", DEVTYPE=="usb_device", ATTRS{idVendor}=="xxxx", ATTR{power/autosuspend}="-1"
  ```
- **NVMe I/O scheduler udev rules:** Modern kernels removed the `queue/scheduler` file for NVMe devices (it's always `none`). Rules targeting `ATTR{queue/scheduler}` on NVMe partitions produce boot-time sysfs errors. Use `SUBSYSTEM=="nvme"` to match only the NVMe controller.
- **BERT "Skipped 1 error records"** is almost always a firmware/BIOS quirk on Gigabyte boards. It's not actionable unless rasdaemon can decode the CPER record. Don't chase it unless there are actual system crashes.
- **USB wakeup paths are hardware-dependent** and can change when you plug into different ports. Service files with hardcoded USB paths (e.g., `/sys/bus/usb/devices/3-7/power/wakeup`) will break if topology changes. Prefer `udev` rules with `VID/PID` matching for USB wake control.
