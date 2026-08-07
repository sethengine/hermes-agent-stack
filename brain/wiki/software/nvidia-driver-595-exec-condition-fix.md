---
category: software
source_session: 20260702_180259_6c64a4
date: 2026-07-02
tags: [nvidia, suspend, resume, exec-condition, systemd, manjaro]
---

# NVIDIA Driver 595+ ExecCondition Fix

## Problem

NVIDIA driver **595.71.05** changed its module license string from `"NVIDIA"` to `"Dual MIT/GPL"`. This breaks the stock systemd suspend/resume/hibernate services (`nvidia-suspend.service`, `nvidia-resume.service`, `nvidia-hibernate.service`) because their `ExecCondition` runs:

```bash
/usr/bin/modinfo -F license nvidia | grep -q 'NVIDIA'
```

This returns exit code 1 for `"Dual MIT/GPL"`, causing all three services to be **skipped every suspend/resume cycle**. The GPU state is never properly saved/restored.

## Symptoms

After resume from sleep:
- Black screen with monitor signal (white LED, not blinking/no-signal)
- Kernel log: `kwin_wayland: Atomic modeset test failed! Permission denied`
- Kernel log: `kwin_wayland: Applying output configuration failed!`
- Journal: `nvidia-resume.service: Skipped due to 'exec-condition'`

## Fix

Create systemd drop-in overrides that fix the license check to match both old and new license strings:

```bash
sudo mkdir -p /etc/systemd/system/nvidia-suspend.service.d \
             /etc/systemd/system/nvidia-resume.service.d \
             /etc/systemd/system/nvidia-hibernate.service.d
```

Each override file contains:
```ini
[Service]
ExecCondition=
ExecCondition=/bin/sh -c "/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'"
```

Then `sudo systemctl daemon-reload` to apply.

## Verification

```bash
/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'; echo $?
# Should return 0
systemctl cat nvidia-suspend.service | grep ExecCondition
```

## Affected Systems

- NVIDIA driver version >= 595.x on any distribution (found on Manjaro Linux)
- [[nvidia-suspend-resume-services]] — the systemd services for NVIDIA sleep state handling
- See also: [[nvidia-black-screen-on-sleep-wake]]
