---
source_session: "20260711_133313_2ff88a"
date: 2026-07-11
category: gpu
related: [nvidia-edid-firmware-fix, resume-hook-dp-toggle, hp-x34-display]
---

# NVIDIA DRM Post-Sleep Fake NVD EDID

After system sleep/wake, the NVIDIA DRM driver fails to re-read the monitor's EDID over DisplayPort and substitutes a **fake 128-byte "NVD" placeholder EDID**.

## Symptoms

- Display locked at **640×480@60Hz** after resume
- `edid-decode` shows manufacturer `NVD` (NVIDIA), not the real monitor manufacturer
- All four detailed timing descriptors are empty — only DMT 0x04 (640×480) available
- Kernel log on resume: `Failed to register auto-value-update on pre-wait value for sync FD semaphore surface`
- `kscreen-doctor` trying to set the real resolution SIGABRT core dumps because 3440×1440@165 doesn't exist in the fake mode list

## Root Cause

The NVIDIA GPU's DisplayPort receiver fails link re-negotiation after S3 resume. The driver can't reach the monitor via DDC (Display Data Channel) and falls back to a built-in minimal EDID blob (manufacturer code `NVD`).

## Affected Hardware

- HP X34 ultrawide (3440×1440@165) via DisplayPort
- Likely affects any DP-connected monitor on NVIDIA GPUs with GSP firmware enabled
- [[nvidia-edid-firmware-fix]] for the permanent solution
