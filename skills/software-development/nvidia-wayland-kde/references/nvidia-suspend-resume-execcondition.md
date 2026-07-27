# NVIDIA Suspend/Resume ExecCondition Bug (Driver 595+)

## Detection Pattern

- **Monitor:** White LED (signal detected) but black screen after system suspend/resume
- **System:** USB/keyboard/network resume normally — just the display pipeline is dead
- **KWin journal:** `Atomic modeset test failed! Permission denied`
- **Resume service:** `nvidia-resume.service: Skipped due to 'exec-condition'.`

## The Bug

NVIDIA driver 595+ changed its kernel module license from `"NVIDIA"` to `"Dual MIT/GPL"`:

```bash
# BEFORE (driver 545, 550, 555, 565):
$ modinfo -F license nvidia
NVIDIA

# AFTER (driver 595+):
$ modinfo -F license nvidia
Dual MIT/GPL
```

The shipped systemd services (`nvidia-suspend.service`, `nvidia-resume.service`, `nvidia-hibernate.service`) have this `ExecCondition`:

```
ExecCondition=/bin/sh -c "/usr/bin/modinfo -F license nvidia | grep -q 'NVIDIA'"
```

- Old driver → `modinfo` returns `NVIDIA` → `grep -q 'NVIDIA'` exits 0 → **service runs** ✓
- Driver 595+ → `modinfo` returns `Dual MIT/GPL` → `grep -q 'NVIDIA'` exits 1 → **service skipped** ✗

## Who Is Affected

- **All RTX 50-series (Blackwell)** — always on nvidia-open, driver 570+ minimum
- **Any GPU on driver 595+** — RTX 40-series (Ada) running newer driver branches
- **Manjaro, Arch, EndeavourOS** using the 595.x branch from `linux-mainline` or `nvidia-595xx` packages

## Full Journal Trace

```
# Systemd skips the resume action
systemd[1]: Starting NVIDIA system resume actions...
systemd[1]: nvidia-resume.service: Skipped due to 'exec-condition'.
systemd[1]: Condition check resulted in NVIDIA system resume actions being skipped.

# A few seconds later KWin tries to modeset and fails
kwin_wayland[1762]: atomic commit failed: Permission denied

# Eventually KWin gives up and crashes the session
kwin_wayland[1762]: Atomic modeset test failed! Permission denied
kwin_wayland[1762]: Applying output configuration failed!
kwin_wayland[1762]: The X11 connection broke (error 1)
systemd[1045]: Stopping KDE Wayland Compositor...
```

## What Actually Happens on Resume

```
Monitor receives signal (white LED)          ← Good
↓
USB/keyboard/network wake                    ← Good
↓
KWin tries atomic modeset via nvidia_drm     ← Fails "Permission denied"
↓
Monitor stays black                          ← Bad
↓
KWin compositor crashes (PipeWire error)
↓
Session dies → SDDM reappears
```

The nvidia-resume.service is supposed to restore GPU VRAM state and reinitialize the display hardware. Without it, the GPU is in an undefined state and the DRM driver refuses KWin's modeset request.

## The Fix

Create systemd drop-in overrides that fix the `ExecCondition`:

```bash
sudo mkdir -p /etc/systemd/system/nvidia-suspend.service.d \
             /etc/systemd/system/nvidia-resume.service.d \
             /etc/systemd/system/nvidia-hibernate.service.d

for svc in nvidia-suspend nvidia-resume nvidia-hibernate; do
  sudo tee /etc/systemd/system/$svc.service.d/override.conf << 'EOF'
[Service]
# Driver 595+ reports "Dual MIT/GPL" — match both old and new
ExecCondition=
ExecCondition=/bin/sh -c "/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'"
EOF
done

sudo systemctl daemon-reload
```

Key points about the fix:
- **Drop-in overrides** survive driver package updates (files live in `/etc/systemd/system/`, not in package-managed `/usr/lib/systemd/system/`)
- `ExecCondition=` (empty reset) removes the old failing condition
- The replacement `grep -qiE 'nvidia|mit/gpl'` matches both `"NVIDIA"` (old) and `"Dual MIT/GPL"` (595+), case-insensitive
- All three services (suspend, resume, hibernate) need the same fix

## Verification

```bash
# Check the drop-in is active
systemctl cat nvidia-resume.service | grep ExecCondition

# Test the condition passes
/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'; echo $?
# Output: 0

# After next suspend/resume, check the service ran
journalctl -b --no-hostname | grep "nvidia-resume.service\\|NVIDIA system resume"
# Should show "Deactivated successfully.", not "Skipped due to 'exec-condition'."
```

## Related

- This is a different failure mode from DPMS display-off wake (GSP link training). Both produce a black screen, but the DPMS version has no system suspend involved and has different fixes (RMUseSwLinkTraining, GSP disable).
- The ExecCondition bug affects only system suspend/resume/hibernate cycles, not display power-off timeouts.
