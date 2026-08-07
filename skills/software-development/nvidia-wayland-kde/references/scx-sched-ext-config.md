# scx / sched-ext Config Pitfalls

## Config Typo That Breaks scx_loader

On Arch/Manjaro, `scx_loader.service` reads config from `/usr/share/scx_loader/config.toml`. A case mismatch in `default_mode` causes `systemctl status scx_loader` to show:

```
scx_loader[777]: unknown variant `gaming`, expected one of `Auto`, `Gaming`, `PowerSave`, `LowLatency`, `Server`
```

The allowed values use **capital first letter** (`Gaming`, not `gaming`). Fix:

```bash
sudo sed -i 's/"gaming"/"Gaming"/' /usr/share/scx_loader/config.toml
```

Or for any case mismatch:
```bash
sudo sed -i 's/default_mode = "[a-z]*"/default_mode = "Gaming"/' /usr/share/scx_loader/config.toml
```

After fixing, start the scheduler directly:
```bash
sudo scx_rustland --gaming
```

Or via scxctl:
```bash
sudo scxctl start -s rustland -m Gaming
```

Note: The config file also sets `default_sched = "scx_rustland"`, so fixing the mode and restarting `scx_loader.service` will auto-start it on next boot.

## scx_rustland Crash on Intel Arrow Lake After Suspend/Resume

### Root Cause

On Intel Arrow Lake (Core Ultra 200-series, Z890), the kernel's CPU topology exposed via `sysfs` becomes inconsistent after resume from suspend. Specifically, the cluster/L1d cache topology conflicts:

```
hwloc 2.9.2 received invalid information from the operating system.
Failed with: intersection without inclusion
while inserting Group0 (P#24 cpuset 0x00000f00) at L1d (P#24 cpuset 0x00000110)
coming from: linux:sysfs:cluster
```

`cpuset 0x00000f00` = CPUs 8-11, `cpuset 0x00000110` = CPUs 4, 8. The cluster view and the cache view disagree on which CPUs share an L1d cache. This confuses hwloc, which scx_rustland uses for topology detection, causing scx_rustland to **SIGABRT** at resume.

### Crashes Cascade

The crash is followed by:
- `kwin_wayland: Atomic modeset test failed! Permission denied`
- `kwin_wayland: Applying output configuration failed!`
- DMAR fault: `[INTR-REMAP] Request device [02:00.1] fault reason 0x22` (NVIDIA HDMI audio interrupt remapping stale after resume)

### Fix Options

**Option A — Switch to scx_bpfland (recommended, no hwloc)**

`scx_bpfland` is written in C, uses the same latency-focused algorithm as scx_rustland but runs entirely in BPF kernel-space. It does NOT use hwloc for topology detection, so the resume topology inconsistency does not affect it.

```bash
sudo mkdir -p /etc/scx_loader
sudo tee /etc/scx_loader/config.toml << 'EOF'
default_sched = "scx_bpfland"
default_mode = "Gaming"
EOF
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader SwitchScheduler su "scx_bpfland" 1
```

**Option B — Restart scx_rustland on resume**

```bash
sudo tee /etc/systemd/system/restart-scx-after-resume.service << 'EOF'
[Unit]
Description=Restart scx scheduler after resume
After=suspend.target hibernate.target hybrid-sleep.target

[Service]
Type=oneshot
ExecStart=/usr/bin/busctl call org.scx.Loader /org/scx/Loader org.scx.Loader RestartScheduler
TimeoutSec=30

[Install]
WantedBy=suspend.target hibernate.target hybrid-sleep.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable restart-scx-after-resume.service
```

**Option C — Switch to default kernel scheduler (EEVDF)**

```bash
sudo systemctl disable --now scx_loader.service
```

### udev + intel_pstate Combo for E-core Stutter Prevention

When games land on E-cores causing stutter on hybrid Intel, scx_bpfland with Gaming mode + `intel_pstate=passive` + performance governor forces P-core-only scheduling:

```bash
# Add to GRUB_CMDLINE_LINUX_DEFAULT
intel_pstate=passive

# Then regenerate GRUB
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

scx_bpfland Gaming mode applies `-m performance -c 0` flags. For more details see the r/Bazzite discussion and CachyOS sched-ext docs.

## scx_loader DBUS API Reference

The scx_loader exposes a DBUS interface at `org.scx.Loader` on the system bus. Available methods:

```bash
# Check current scheduler
busctl get-property org.scx.Loader /org/scx/Loader org.scx.Loader CurrentScheduler

# List all supported schedulers
busctl get-property org.scx.Loader /org/scx/Loader org.scx.Loader SupportedSchedulers

# Switch scheduler (s=name, u=mode 1=Gaming)
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader SwitchScheduler su "scx_bpfland" 1

# Restart current scheduler
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader RestartScheduler

# Stop scheduler (falls back to kernel EEVDF)
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader StopScheduler

# Restore default from config
busctl call org.scx.Loader /org/scx/Loader org.scx.Loader RestoreDefault
```

## When scx_rustland Actually Helps

scx_rustland uses deadline-based scheduling in userspace. On a kernel already tuned with `preempt=full`, `nohz_full`, `rcu_nocbs`, and `performance` governor, the gains over CFS are marginal (2-5% smoother frame times in games). It does NOT fix IRQ-related freezes (those are interrupt routing + C-state issues, not scheduler issues).

The scheduler provides better P-core/E-core task placement than CFS for mixed workloads (gaming + streaming), but on a system where IRQs are already pinned and P-cores are isolated, most of that benefit is already achieved through other means.

## Service Status

```bash
# Check
systemctl status scx_loader

# Config location
cat /usr/share/scx_loader/config.toml

# Available modes
scx_rustland --help | grep -i mode

# If running, verify scheduler is active
cat /sys/kernel/sched_ext/state  # "enabled" if a scx scheduler is running
```
