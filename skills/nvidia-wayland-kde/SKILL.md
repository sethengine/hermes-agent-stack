---
name: nvidia-wayland-kde
description: Troubleshoot NVIDIA GPU + Wayland + KDE Plasma desktop on Arch Linux — Chrome GPU rendering, PowerDevil display management, input latency, display wake failures, compositor issues, environment variable tuning, and Proton game settings/frame limiter fixes.
category: software-development
tags:
  - nvidia
  - wayland
  - kde
  - plasma
  - chrome
  - display
  - powerdevil
  - arch
trigger: /nvidia-wayland
---

# NVIDIA + Wayland + KDE Desktop Troubleshooting

> **Style note for this user:** They prefer a direct answer first, then supporting detail. When they ask a yes/no question, answer it immediately before explaining the reasoning. Long preambles before addressing the actual question will be called out. Keep explanations after the verdict, not before.
> **Shell commands:** Give exact copy-paste commands in a single code block per command. Do NOT use `\` line continuations in multi-line commands — the user's zsh will parse the `\n` as a literal newline and error with "zsh: parse error". Each command must be a single line or a proper multi-line block zsh can parse. Never try to run commands for them — give the commands and let the user execute them.

## Overview

This skill covers the known-problematic combination of NVIDIA proprietary driver + Wayland display server + KDE Plasma desktop on Arch-based Linux (Manjaro, Arch, EndeavourOS). The stack has known gaps — DPMS state monitoring, display wake reliability, Chrome GPU acceleration, and compositor smoothness.

## Quick Diagnostic Sweep

Run these to snapshot the system state when a user reports issues:

```bash
# GPU state
nvidia-smi --query-gpu=name,driver_version,memory.total,power.limit,temperature.gpu,utilization.gpu,pstate --format=csv

# Chrome flags in use (if Chrome running)
cat /proc/$(pgrep -o chrome 2>/dev/null | head -1)/cmdline 2>/dev/null | tr '\0' ' ' | grep -oP '(?<=--)[a-z-]+'

# KWin compositor config
cat ~/.config/kwinrc 2>/dev/null

# Screen locker settings
cat ~/.config/kscreenlockerrc 2>/dev/null

# Power management profiles
cat ~/.config/powerdevilrc 2>/dev/null
cat ~/.config/powermanagementprofilesrc 2>/dev/null

# Environment variables affecting NVIDIA/Wayland
env | grep -iE "WAYLAND|__GL|KWIN_DRM|GBM_BACKEND|GDK_BACKEND|QT_QPA|MOZ_ENABLE_WAYLAND|LIBVA_DRIVER|VK_DRIVER"

# Chrome flags config
cat ~/.config/chrome-flags.conf 2>/dev/null

# Kernel cmdline
cat /proc/cmdline

# Log sweep for display/GPU/suspend errors
journalctl -b -p err --no-hostname 2>/dev/null | head -40
dmesg | grep -iE "drm|nvidia|dpms|sleep|suspend|resume|blank|modeset|hotplug" | tail -30
```

## Chrome GPU Acceleration (NVIDIA Wayland)

### The SwiftShader Trap

On Chrome/Chromium 148+ with NVIDIA + Wayland, `--use-gl=angle` **without** `--use-angle=vulkan` causes ANGLE to fall back to **SwiftShader** (software renderer) for WebGL/Canvas. This makes WebGL-heavy apps (GeoGuessr, Google Maps, Figma) run on CPU.

### MangoHud Pitfall: vulkan_present_mode=immediate + fps_limit=0 = no cap

Setting `vulkan_present_mode=immediate` in MangoHud.conf tells the Vulkan driver to present frames as fast as possible with zero waiting. This **overrides both vsync and fps_limit** — MangoHud cannot cap FPS when immediate mode is active because the Vulkan present queue never waits.

Symptoms:
- MangoHud overlay shows FPS and stats but FPS stays uncapped
- GPU usage at 99% even with `fps_limit` set
- User thinks "mangohud has no limit for fps"

Fix:
```ini
# Remove or comment out immediate mode:
# vulkan_present_mode=immediate

# Use mailbox instead for low-latency with capping:
vulkan_present_mode=mailbox
```

Also ensure `fps_limit` is a **non-zero value** — `fps_limit=0` means unlimited:

```ini
fps_limit=60    # Real cap
# fps_limit=0  # UNLIMITED — no cap at all
```

### ⚠️ Critical: `--use-angle=gl` causes "Network connection interrupted" on ALL pages

Adding `--use-angle=gl` alongside `--use-gl=angle` (i.e. `--use-gl=angle --use-angle=gl`) causes ANGLE to use the OpenGL backend directly. On NVIDIA Wayland with Chrome 149+, this produces **"Network connection interrupted" errors on every page** — the GPU process crashes or stalls, which takes down Chrome's network service (they share GPU-accelerated networking paths like QUIC).

**Fix:** Remove `--use-angle=gl`. Keep only `--use-gl=angle` — let ANGLE auto-detect its backend. On NVIDIA Wayland, ANGLE's default GL backend (not explicitly `--use-angle=gl`) is the only working path.

**Tradeoff:** Removing `--use-angle=gl` can introduce **YouTube A/V desync** when hardware video decode (VA-API) is active — see the VA-API ZeroCopyGL pitfall below.

### ⚠️ Critical: `--use-gl=egl` crashes GPU process on NVIDIA + Wayland

`--use-gl=egl` causes Chrome's GPU process to fail to boot. The GPU process crashes during EGL display initialization, and Chrome disables ALL hardware acceleration:

```
GPU process was unable to boot: GPU access is disabled due to frequent crashes.
                                                         Disabled Features: all
```

The correct flag is **always** `--use-gl=angle` on NVIDIA + Wayland. The ANGLE OpenGL backend (`ANGLE_OPENGL`) is the only working path.

### ⚠️ Critical: `--use-angle=vulkan` + Wayland — AMD vs NVIDIA Difference

Since **Chromium 129** (mid-2024, CL 5568860), `--use-angle=vulkan` on Wayland was unblocked upstream. This works for **AMD/Intel** GPUs with Mesa RADV driver. For those GPUs, it enables a better Vulkan rendering path for VAAPI video decode.

On **NVIDIA + Wayland**: `--use-angle=vulkan` still **crashes the GPU process**. Chrome logs:

```text
'--ozone-platform=wayland' is not compatible with Vulkan.
Consider switching to '--ozone-platform=x11' or disabling Vulkan
Failed to retrieve vkGetInstanceProcAddr pointer from ANGLE.
Failed to create and initialize Vulkan implementation.
```

Although `chrome://gpu` in Chrome 149+ shows "Vulkan: Enabled" with API 1.4.350 and a populated Vulkan Information section, the ANGLE Vulkan backend (`--use-angle=vulkan`) fails during GPU process initialization on NVIDIA + Wayland. The **Vulkan backend is not usable** on this combination.

**Vulkan Video decode on Chrome is not possible on NVIDIA Wayland.** Video decode must use the VAAPI path.

### ⚠️ Critical: Flag conflict — features in both `--enable-features` and `--disable-features`

Having the same feature in BOTH lists cancels it. Chrome uses the disable list as the authoritative source:
```
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
--disable-features=UseMultiPlaneFormatForHardwareVideo,VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
```
Net result: VAAPI is **disabled** — Video Acceleration Information is EMPTY in chrome://gpu.

### Recommended chrome-flags.conf

Location: `~/.config/chrome-flags.conf` (Arch wrapper reads this automatically)

**Working config for NVIDIA + Wayland (Video + GPU acceleration):**
```\n--ozone-platform=wayland\n--use-gl=angle\n--ignore-gpu-blocklist\n--enable-gpu-rasterization\n--enable-native-gpu-memory-buffers\n--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL,UseMultiPlaneFormatForHardwareVideo\n```\n\nFlag breakdown:\n\n| Flag | Purpose |\n|------|---------|\n| `--use-gl=angle` | REQUIRED — only working GL path on NVIDIA+Wayland |\n| `--ignore-gpu-blocklist` | Enables GPU despite Chrome's blocklist |\n| `--enable-gpu-rasterization` | GPU raster for page rendering |\n| `--enable-native-gpu-memory-buffers` | Needed for zero-copy video decode |\n| `VaapiOnNvidiaGPUs` | **Key flag** — enables VAAPI on NVIDIA GPUs on Chrome 149+ |\n| `VaapiIgnoreDriverChecks` | Bypasses Chrome's `Should skip nVidia device` check in vaapi_wrapper.cc |\n| `AcceleratedVideoDecodeLinuxGL` | VAAPI decode path via GL |\n| `UseMultiPlaneFormatForHardwareVideo` | Keeps YUV as multi-plane textures (better quality) |\n\n**Note on `AcceleratedVideoDecodeLinuxZeroCopyGL`:** This flag is deliberately NOT in the recommended config. On NVIDIA Wayland, zero-copy VA-API decode causes YouTube A/V desync (see the dedicated pitfall section below). Only add it if you need the performance gain and can tolerate the sync issue.

### Enabling VAAPI video decode on NVIDIA

Even with correct flags, Chrome has a **built-in check** that skips NVIDIA DRM devices:
```
Should skip nVidia device named: nvidia-drm
```
This requires BOTH `VaapiOnNvidiaGPUs` AND `VaapiIgnoreDriverChecks` in `--enable-features`. Without both, Video Acceleration Information in chrome://gpu stays empty.

### ⚠️ Pitfall: `AcceleratedVideoDecodeLinuxZeroCopyGL` causes YouTube A/V desync on NVIDIA Wayland

The zero-copy VA-API decode path (`AcceleratedVideoDecodeLinuxZeroCopyGL`) passes decoder output directly to the GL renderer without copying. On NVIDIA's proprietary driver, the frame pacing from this path is unreliable — frames arrive at irregular intervals, causing the video clock to drift from the audio clock.

**Symptom:** YouTube audio/video gradually drifts out of sync (audio ahead of video) when hardware decode is active. Only affects videos using GPU decoding (check `chrome://media-internals`).

**The tradeoff is unavoidable on NVIDIA Wayland:**
- `--use-angle=gl` removed → fixes "network connection interrupted" but VA-API with ZeroCopyGL desyncs YouTube
- `AcceleratedVideoDecodeLinuxZeroCopyGL` removed → fixes YouTube sync but VA-API decode uses the copy path (slightly higher CPU, may cause stutter on 4K)

**Possible fixes (in order of likelihood):**

1. Remove `AcceleratedVideoDecodeLinuxZeroCopyGL` from `--enable-features`, keep the rest. Hardware decode still works via the copy path — frame pacing is correct.
2. If still desynced, try `--use-angle=vulkan` with `--use-gl=angle` — on some NVIDIA driver versions, Vulkan's swapchain handles zero-copy DMA-BUF frames better than GL. On others, Vulkan + Wayland crashes the GPU process — test.
3. Switch to ANGLE's Vulkan backend: `--use-angle=vulkan` — only works on certain Chrome + driver combinations (see Critical section above).

The root cause is NVIDIA's VA-API driver (`libva-nvidia-driver`) not properly implementing DMA-BUF modifier negotiation for zero-copy — the frames arrive but with incorrect presentation timestamps.

### Required environment variables

```bash
export LIBVA_DRIVER_NAME=nvidia          # Loads the elFarto libva-nvidia-driver
export NVD_BACKEND=direct                # Direct NVDEC backend, not VDPAU wrapper
```

### Verify in chrome://gpu

After applying flags, check:

- ✅ Compositing: Hardware accelerated
- ✅ Rasterization: Hardware accelerated on all pages
- ✅ Video Decode: Hardware accelerated
- ✅ Video Acceleration Information — populated with decode profiles (H.264, VP9, AV1)
- ⚠️ Vulkan: Disabled (expected — does not work on Wayland)
- ❌ No "GPU process was unable to boot" or "Software only" entries

### When the GPU process crashes

If chrome://gpu shows "GPU process was unable to boot", the most likely cause is `--use-gl=egl`. Revert to `--use-gl=angle` and restart Chrome.

### Flag Reference

| Flag | Effect |
|------|--------|
| `--ignore-gpu-blocklist` | Enables GPU despite Chrome's blocklist |
| `--disable-gpu-driver-bug-workarounds` | Stops Chrome from crippling NVIDIA with defensive hacks |
| `--use-gl=angle --use-angle=vulkan` | ANGLE with Vulkan backend — only for AMD/Intel on Wayland. **DOES NOT WORK** on NVIDIA Wayland (Vulkan init fails). |
| `--use-gl=desktop` | Native OpenGL (fallback if Vulkan unstable) |
| `--enable-native-gpu-memory-buffers` | **Do NOT use** on NVIDIA Wayland — causes rendering corruption |

### Verify in chrome://gpu

After applying flags, check:
- ✅ WebGL / WebGL2: Hardware accelerated
- ✅ Canvas: Hardware accelerated
- ✅ GPU rasterization: Enabled
- ⚠️ Vulkan: Disabled on NVIDIA Wayland (expected — Vulkan + Wayland + NVIDIA is not compatible). On AMD/Intel, ✅ Vulkan: Initialized is expected.
- ❌ SwiftShader should NOT appear anywhere

## Chrome Middle-Click Autoscroll (MiddleClickAutoscroll)

### The Problem

Chrome's autoscroll feature (press middle mouse button → move mouse up/down to scroll) is **disabled by default on Linux**. In the Chromium source, `MiddleClickAutoscroll` is only enabled for Windows:

```cpp
// enabled only for Windows
if (runtime_flags::isWindows) {
    enableFeature("MiddleClickAutoscroll");
}
```

This applies to all Chromium-based browsers on Linux (Chrome, Edge, Brave, Vivaldi).

### The Fix

Add `--enable-features=MiddleClickAutoscroll` to `~/.config/chrome-flags.conf`:

```bash
echo '--enable-features=MiddleClickAutoscroll' >> ~/.config/chrome-flags.conf
```

**⚠️ CRITICAL: Use `--enable-features`, NOT `--enable-blink-features`.** Both flags enable the same autoscroll feature, but `--enable-blink-features=MiddleClickAutoscroll` causes Chrome to display a "stability and security will suffer" warning banner at the top of every page. The `--enable-features` form enables the same Blink runtime feature without triggering the unsupported-flag warning. Per the [ArchWiki](https://wiki.archlinux.org/title/Chromium#Enabling_autoscroll_with_middle_mouse_button): "While setting `--enable-blink-features` works in the same way as only typing `--enable-features`, the browser instead may display a warning."

## ⚠️ Pitfall: `AcceleratedVideoDecodeLinuxZeroCopyGL` causes YouTube A/V desync on NVIDIA Wayland

The zero-copy VA-API decode path (`AcceleratedVideoDecodeLinuxZeroCopyGL`) passes decoder output directly to the GL renderer without copying. On NVIDIA's proprietary driver, the frame pacing from this path is unreliable — frames arrive at irregular intervals, causing the video clock to drift from the audio clock.

**Symptom:** YouTube audio/video gradually drifts out of sync (audio ahead of video) when hardware decode is active. Only affects videos using GPU decoding (check `chrome://media-internals`).

**Root cause:** NVIDIA's VA-API driver (`libva-nvidia-driver`) does not properly implement DMA-BUF modifier negotiation for zero-copy. The frames arrive with incorrect presentation timestamps, and ANGLE's GL backend cannot compensate for the timing drift.

**Fix:** Remove `AcceleratedVideoDecodeLinuxZeroCopyGL` from the `--enable-features` list. Hardware decode still works via the copy path — the non-zero-copy path (`AcceleratedVideoDecodeLinuxGL`) does proper frame pacing.

**This is a permanent tradeoff on NVIDIA Wayland:** zero-copy gives better performance with broken sync; the copy path gives correct sync with slightly higher CPU usage (negligible on modern hardware like the RTX 5060 Ti).

## Chrome Launch Chain (Arch/Manjaro)

```

The launch chain:

```
~/.local/share/applications/google-chrome.desktop
  Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable %U
  → /usr/bin/google-chrome-stable (shell wrapper)
    → reads ~/.config/chrome-flags.conf (grep -v '^#' → $CHROME_USER_FLAGS)
    → /opt/google/chrome/google-chrome $CHROME_USER_FLAGS "$@"
```

The wrapper script at `/usr/bin/google-chrome-stable`:

```bash
#!/bin/bash
XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-~/.config}
if [[ -f $XDG_CONFIG_HOME/chrome-flags.conf ]]; then
    CHROME_USER_FLAGS="$(grep -v '^#' $XDG_CONFIG_HOME/chrome-flags.conf)"
fi
exec /opt/google/chrome/google-chrome $CHROME_USER_FLAGS "$@"
```

The `.desktop` file in `~/.local/share/applications/` takes precedence over the system one in `/usr/share/applications/`. This is where custom env vars (LIBVA_DRIVER_NAME, NVD_BACKEND) are set alongside the browser path.

### Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Flag removed when editing `chrome-flags.conf` | Autoscroll stops working after unrelated config change | Always check `chrome-flags.conf` still has `MiddleClickAutoscroll` after editing |
| No flag anywhere (not in `.desktop`, not in `chrome-flags.conf`) | Middle-click does nothing or pastes | Add the flag — it's the only way on Chrome Linux |
| Middle-click still pastes (KDE Wayland) | Autoscroll icon appears but immediately pastes | Disable KDE's middle-click paste: System Settings → Input Devices → Mouse → untick "Paste on middle click" |
| Chrome version updated | Desktop file overwritten by Chrome update | `chrome-flags.conf` is the safest place — survives any .desktop reset |

### Verification

```bash
# Confirm flag is loaded
cat /proc/$(pgrep -o chrome 2>/dev/null | head -1)/cmdline 2>/dev/null | tr '\0' ' ' | grep -o 'MiddleClickAutoscroll'
# If empty, Chrome needs restart

# Or check chrome://version — look for MiddleClickAutoscroll in "Command Line"
```

### Related Issue

Chromium bug tracker: [Linux version lacks autoscroll (Issue 40811836)](https://issues.chromium.org/issues/40811836) — starred to track when they finally expose the UI option.

## PowerDevil + DPMS Display Wake Failures

### Known Bug

KDE PowerDevil on NVIDIA Wayland logs:
```
org_kde_powerdevil: Watching for DPMS state changes unimplemented
```

This is a NVIDIA driver integration gap — PowerDevil can't monitor display power state changes on Wayland + NVIDIA. This causes:

- Display blanking → monitor stays black on wake
- Keyboard backlights briefly flash on keypress but screen stays dark
- The system may partially suspend (USB devices wake, but display pipeline fails)

### Investigation Steps

```bash
# Check if PowerDevil is crashing/restarting in a loop
journalctl -b --no-hostname | grep org_kde_powerdevil | tail -20

# Check powerdevil configs
cat ~/.config/powerdevilrc
cat ~/.config/powermanagementprofilesrc

# Check idle inhibitors
qdbus6 org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/PolicyAgent \
  org.kde.Solid.PowerManagement.PolicyAgent.ListInhibitions --literal
```

### System Suspend/Resume Wake Failure (NVIDIA 595+ ExecCondition Bug)

A distinct wake-failure mode from DPMS display-off: the system suspends via `systemctl suspend` or idle timeout, wakes on input — the monitor lights up (white LED = signal detected), but **stays black** because KWin can't modeset.

#### Root Cause

Starting with **NVIDIA driver 595**, the kernel module's license string changed from `"NVIDIA"` to `"Dual MIT/GPL"`:

```bash
$ modinfo -F license nvidia
Dual MIT/GPL
```

The shipped `nvidia-suspend.service`, `nvidia-resume.service`, and `nvidia-hibernate.service` all check:

```
ExecCondition=/bin/sh -c "/usr/bin/modinfo -F license nvidia | grep -q 'NVIDIA'"
```

The grep for `'NVIDIA'` fails (exit 1) because the string is now `"Dual MIT/GPL"`. Systemd skips the service:

```
nvidia-resume.service: Skipped due to 'exec-condition'.
Condition check resulted in NVIDIA system resume actions being skipped.
```

Without the resume action, the GPU state is never restored. On wake, KWin gets `Permission denied` from the NVIDIA DRM driver:

```
kwin_wayland: Atomic modeset test failed! Permission denied
kwin_wayland: Applying output configuration failed!
```

The system resumes (USB, keyboard, network all work) but the display pipeline is dead. Full diagnosis in `references/nvidia-suspend-resume-execcondition.md`.

#### Fix — systemd drop-in overrides (survive driver updates)

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

#### Verify

```bash
# Check drop-ins are loaded
systemctl cat nvidia-resume.service | grep ExecCondition

# Test the new condition passes
/usr/bin/modinfo -F license nvidia | grep -qiE 'nvidia|mit/gpl'; echo $?
# Should print 0
```

### Fixes

**Disable auto-suspend (primary fix):**
```bash
kwriteconfig6 --file powermanagementprofilesrc --group AC --group SuspendAndShutdown --key AutoSuspendIdleTimeoutSec 0
systemctl --user restart plasma-powerdevil
```

**Disable display-off if blanking triggers the wake failure:**
```bash
kwriteconfig6 --file powerdevilrc --group AC --group Display --key TurnOffDisplayIdleTimeoutSec 0
systemctl --user restart plasma-powerdevil
```

**Check IgnoreIdleInhibitors:**
If `IgnoreIdleInhibitors=true` in `~/.config/powerdevilrc`, the system ignores "don't sleep" signals from Steam/Chrome/TF2, causing sleep during active use. Set to `false` or remove the key.

### Inhibiting via D-Bus (runtime only)

```bash
qdbus6 org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/PolicyAgent \
  org.kde.Solid.PowerManagement.PolicyAgent.AddInhibition 6 "app-name" "reason"

# Release:
qdbus6 org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/PolicyAgent \
  org.kde.Solid.PowerManagement.PolicyAgent.ReleaseInhibition <cookie>
```

Types bitmask: 1=Logout, 2=Suspend, 4=Screen off, 6=both suspend+screen.

## plasmashell Crash on NVIDIA Wayland: DRM Syncobj FD Leak

### Symptom

After 12-16 hours of uptime, plasmashell (KDE taskbar/desktop shell) freezes, then exits. Windows close and reappear. The journal shows:

```
plasmashell: error marshalling arguments for import_timeline: dup failed: Too many open files
plasmashell: Error marshalling request for wp_linux_drm_syncobj_manager_v1.import_timeline: Too many open files
plasmashell: eglSwapBuffers failed with 0x3000
plasmashell: The Wayland connection experienced a fatal error: Too many open files
systemd: plasma-plasmashell.service: Main process exited, code=exited, status=255/EXCEPTION
systemd: plasma-plasmashell.service: Scheduled restart job, restart counter is at 1.
```

### Root Cause

The NVIDIA **open kernel module** (`nvidia-open`) leaks file descriptors through the Wayland `wp_linux_drm_syncobj_manager_v1.import_timeline` protocol. Every frame plasmashell renders, KWin sends it a DRM syncobj timeline import FD. The open module's Wayland implementation does not properly close these FDs when buffers are released, so plasmashell's FD count climbs until the soft limit is hit.

Default soft limit on systemd user services: **1024** FDs. System hard limit: **524288**.

The proprietary `nvidia` module uses a different DRM syncobj code path that does NOT have this leak.

### Diagnostic

```bash
# Check current FD count and limits
ls /proc/$(pgrep -o plasmashell)/fd | wc -l
cat /proc/$(pgrep -o plasmashell)/limits | grep 'open files'

# Confirm the leak in journal
journalctl -b --no-hostname | grep 'import_timeline: Too many open files' | tail -5
```

### Quick Fix — Raise FD Limit (interim, survives driver bug)

```bash
mkdir -p ~/.config/systemd/user/plasma-plasmashell.service.d
tee ~/.config/systemd/user/plasma-plasmashell.service.d/override.conf << 'EOF'
[Service]
LimitNOFILE=65536
EOF
systemctl --user daemon-reload
systemctl --user restart plasma-plasmashell.service
```

Verify:
```bash
cat /proc/$(pgrep -o plasmashell)/limits | grep 'open files'
# Should show: 65536  65536
```

This buys weeks instead of hours before the leak hits the limit again. The underlying leak is still active.

### Permanent Fix — Switch to Proprietary NVIDIA Module

The FD leak is in the **open kernel module only**. The proprietary `nvidia` module does not have this bug. On Manjaro:

```bash
# Check what's installed
pacman -Q | grep linux70-nvidia

# Remove open, install proprietary
sudo pacman -R linux70-nvidia-open
sudo pacman -S linux70-nvidia nvidia-settings
sudo reboot
```

Available options for kernel 7.0 on Manjaro:
| Package | Module Type | Version | FD Leak? |
|---------|------------|---------|----------|
| `linux70-nvidia-open` (current) | Open (MIT/GPL) | 595.71.05 | **Yes** |
| `linux70-nvidia` | Proprietary | 610.43.02 | **No** — different syncobj code path |
| `linux70-nvidia-580xx` | Proprietary | 580.159.04 | **No** — alternative branch |

Both module types support Blackwell GPUs at these versions. The open-vs-proprietary choice is now about features (GSP initramfs handling, Wayland syncobj leaks) rather than hardware compatibility.

### When to Apply This Over the Module Choice Section

Use the quick fix (LimitNOFILE) when you cannot reboot or want to defer the module swap. Use the permanent fix (proprietary module) when you need the leak eliminated at the driver level. See "nvidia-open vs nvidia (proprietary) — Driver Module Choice" below for the full tradeoff comparison.

## nvidia-open vs nvidia (proprietary) — Driver Module Choice for Blackwell

### Blackwell Support

**Blackwell GPUs (RTX 50-series including RTX 5060 Ti) work with BOTH module types.** Earlier claims that "Blackwell requires nvidia-open" were true for the 595 driver era, but the proprietary module at version **610+** (available as `linux70-nvidia` on Manjaro) fully supports Blackwell. There IS a module choice:

| Module | Package (Manjaro kernel 7.0) | License | Wayland Syncobj FD Leak |
|--------|------------------------------|---------|------------------------|
| **nvidia-open** (open kernel module) | `linux70-nvidia-open` | MIT/GPL | **Yes** — see "plasmashell Crash on NVIDIA Wayland" section |
| **nvidia** (proprietary) | `linux70-nvidia` | NVIDIA proprietary | **No** — different DRM syncobj code path |

### The FD Leak Tradeoff

The open kernel module (`nvidia-open`) has a known file descriptor leak through the Wayland `wp_linux_drm_syncobj_manager_v1.import_timeline` protocol that crashes plasmashell after 12-16 hours. The proprietary module uses a different syncobj management code path that does not leak. See the "plasmashell Crash on NVIDIA Wayland" section for full diagnostic and both interim and permanent fixes.

### GSP Implications Per Module Type

**nvidia-open**: GSP firmware can be disabled via `NVreg_EnableGpuFirmware=0`, but requires an initramfs rebuild (`mkinitcpio -P`) because nvidia-open loads from initramfs at early boot. The modprobe config change alone won't take effect until the initramfs is regenerated to include it.

**nvidia (proprietary)**: GSP disable via `NVreg_EnableGpuFirmware=0` takes effect immediately on module reload without initramfs changes — the proprietary module does not load from initramfs.

See `references/nvidia-open-vs-dkms-blackwell.md` for full comparison with community sources, performance data, and known issues per GPU generation.

## GSP Firmware and DisplayPort Link Training

### The Problem

On RTX 40/50 series GPUs (Blackwell architecture), the NVIDIA GSP (GPU System Processor) firmware handles DisplayPort link training — the handshake that negotiates resolution, refresh rate, and link speed when the display wakes from DPMS off. The GSP firmware has a known bug where this handshake fails on certain monitors (HP X34, Dell S-series, some LG ultrawides), resulting in a black screen after DPMS display-off, while the PC and USB devices (keyboard backlight) respond normally.

### The GSP Firmware Stack

```
PowerDevil → KWin → DRM atomic → nvidia_drm → GSP firmware → DisplayPort link training → monitor
                              ↑                                              ↑
                    works fine                            FAILS on DPMS resume (RTX 50 series)
```

### Fix Options

**Option A — Software link training (recommended, targeted):**

Keeps GSP firmware enabled for all other tasks (error recovery, power management) but forces the driver CPU-side to handle DisplayPort link training:

Add `RMUseSwLinkTraining=1` to the `NVreg_RegistryDwords` parameter in `/etc/modprobe.d/nvidia-perf.conf`:

```bash
# Before:
options nvidia ... NVreg_RegistryDwords="RMIntrLockingMode=1;..."

# After:
options nvidia ... NVreg_RegistryDwords="RMIntrLockingMode=1;RMUseSwLinkTraining=1;..."
```

Tradeoff: Monitor wake takes 1-2 seconds longer (software link training negotiates more carefully).

**Exact command to apply — append to existing semicolon-separated RegistryDwords:**

If `/etc/modprobe.d/nvidia-perf.conf` already has:
```
options nvidia ... NVreg_RegistryDwords="RMIntrLockingMode=1;RMNvDecSurfacesPerContext=16"
```

Append to the quoted value:
```bash
sudo sed -i 's/NVreg_RegistryDwords="\(.*\)"/NVreg_RegistryDwords="\1;RMUseSwLinkTraining=1"/' /etc/modprobe.d/nvidia-perf.conf
```

Then reboot (or `rmmod nvidia_drm nvidia_modeset nvidia_uvm nvidia && modprobe nvidia` + restart display manager).

**Option B — Disable GSP entirely (stronger, but removes error recovery):**  

```bash
sudo sed -i 's/^options nvidia /options nvidia NVreg_EnableGpuFirmware=0 /' /etc/modprobe.d/nvidia-perf.conf
```

⚠️ **Requires initramfs rebuild** before it takes effect, because nvidia modules load from initramfs at early boot:

```bash
sudo mkinitcpio -P
sudo reboot
```

To verify GSP is actually disabled after reboot:
```bash
nvidia-smi --query-gpu=gsp.mode.current --format=csv,noheader
# Should show "Disabled"
```

If still "Enabled" after reboot, the modprobe config change wasn't baked into the initramfs. Check `modconf` hook presence in `/etc/mkinitcpio.conf` and rebuild again.

Tradeoff: Removes GSP error recovery — Xid errors from GPU engine crashes (Xid 13, 32) that GSP auto-recovers now become hard lockups.

### Frequency Locking vs C-State Disable — What Actually Matters

Two competing tunings for IRQ cores:
- **C-state disable** (C2/C3 off): Keeps cores awake, no 127-1048 µs wake penalty. **Essential for IRQ cores.**
- **Frequency locking** (scaling_min_freq=max): Keeps cores at max clock even between interrupts. **Unnecessary** if `performance` governor is already active.

With `cpufreq.default_governor=performance`, cores ramp to max in ~10 µs on wake. The C-state wake is 127-1048 µs — 10-100x bigger. C-state disable solves the problem; frequency locking adds 10-20W idle power for zero gain. Skip it.

### When to Use Which

| Scenario | Approach |
|----------|----------|
| DPMS wake black screen, no GPU crashes | Option A (software link training) — safest |
| DPMS wake black screen + GPU crashes (Xid 13/32 from games) | Option A — keeps error recovery |
| Option A doesn't fix it | Option B (disable GSP) as last resort |

### Diagnostic Commands

```bash
# Check GSP status
cat /sys/module/nvidia/parameters/NVreg_EnableGpuFirmware 2>/dev/null

# Check modprobe config
cat /etc/modprobe.d/nvidia*.conf

# Check for Xid errors (previous boots)
journalctl -b -1 --no-hostname | grep -i "xid" | tail -10

# Check for link training failures
journalctl -b --no-hostname | grep -iE "link training|dpms|modeset" | tail -10
```

### PCIe Link Status Diagnostic (Blackwell Stability)

Blackwell GPUs (RTX 50-series) have known PCIe Gen 5 training issues that can cause or worsen GPU stability problems. Check current link status:

```bash
# Check negotiated speed — look for (downgraded) indicators
sudo lspci -vv -s $(lspci | grep NVIDIA | awk '{print $1}') | grep -A2 'LnkSta:'

# Expected output on a healthy Gen 5 link:
#   LnkSta: Speed 32GT/s, Width x16
# Common fallback (Gen 5 training failed):
#   LnkSta: Speed 16GT/s (downgraded), Width x8 (downgraded)
```

- 32GT/s = PCIe 5.0, 16GT/s = PCIe 4.0, 8GT/s = PCIe 3.0
- `(downgraded)` means the initial training failed and the link fell back — this is a known issue on RTX 50-series
- Forcing Gen 4 in BIOS can improve stability with negligible gaming performance impact
- See `references/nvidia-r610-driver-release.md` for more on RTX 5060 Ti PCIe behavior

### GSP Firmware and DisplayPort Link Training

### Symptom

PowerDevil logs on every restart:
```
org_kde_powerdevil: Failed to register with host portal
  QDBusError("org.freedesktop.portal.Error.Failed",
  "Could not register app ID: App info not found for 'org.kde.org_kde_powerdevil'")
```

### Cause

PowerDevil sends `org.kde.org_kde_powerdevil` as its app ID to the portal, but the actual D-Bus name is `org.kde.powerdevil`. The `org_kde_` prefix is a mangled name that doesn't match any installed `.desktop` file. This is a cosmetic bug in KDE 6 — the portal rejects registration but all PowerDevil functionality continues to work.
### Verification

No fix needed — this error is cosmetic. PowerDevil still manages display power, profiles, and suspend correctly.

```bash
# Check if KDE portal backend is running
systemctl --user status plasma-xdg-desktop-portal-kde 2>/dev/null | head -5

# Check which portal backend xdg-desktop-portal chose
journalctl --user -u xdg-desktop-portal --no-hostname -n 3 2>/dev/null

# Check portal files exist
ls /usr/share/xdg-desktop-portal/portals/*.portal 2>/dev/null
```

## sched-ext / scx_loader Config Pitfalls

### The "gaming" vs "Gaming" Typo

scx_loader config uses TOML with enum variants that are **case-sensitive**. A lowercase variant causes scx_loader to crash at boot:

```
Error: TOML parse error at line 5, column 16
   5 | default_mode = "gaming"
     |                ^^^^^^^^
     unknown variant `gaming`, expected one of `Auto`, `Gaming`, `PowerSave`, `LowLatency`, `Server`
```

**Fix:** Capitalise properly:

```bash
sudo sed -i 's/"gaming"/"Gaming"/' /usr/share/scx_loader/config.toml
```

### Finding the Config File

scx_loader looks for config in this order:
1. `/etc/scx_loader.toml`
2. `~/.config/scx_loader.toml`
3. `/usr/share/scx_loader/config.toml` (package default)

On Arch/Manjaro, the default is `/usr/share/scx_loader/config.toml`. Do NOT create `/etc/scx_loader.toml` unless you need to override the defaults — the package default already sets sane defaults.

### When scx_rustland Makes Sense

scx_rustland (Gaming mode) can improve game smoothness on hybrid architectures (P-core + E-core) by making smarter interactive-vs-background task placement than CFS. However:

- **Will NOT fix** IRQ-related freezes, display wake failures, or GPU driver crashes — those are different layers
- **Marginal gain** when kernel is already tuned with `preempt=full`, `nohz_full`, `performance` governor
- **Set up properly**: `scx_ctl start -s rustland -m Gaming` or fix the loader config to auto-start
- **Verify**: `cat /sys/kernel/sched_ext/state` should show the scheduler name, not "disabled"

## I2C Group for DDC/CI Monitor Control

### Purpose

PowerDevil uses DDC/CI (via `/dev/i2c-*` devices) for monitor brightness control and display detection. The devices are owned by `root:i2c` with permissions `crw-rw----`. If the user is not in the `i2c` group, PowerDevil logs:
```
Open failed for /dev/i2c-4, errno=EACCES(-13): Permission denied
```

### Fix

```bash
sudo gpasswd -a $USER i2c
```
Then log out and back in for the group change to take effect.

**Important**: This does NOT fix DPMS wake black screens. DDC/CI is used for brightness and display detection, not for display power state control. DPMS is handled through KWin → DRM → NVIDIA driver. The i2c fix only addresses brightness control and DisplayPort hotplug detection.

## Invisible Mouse Cursor

### Symptom

Cursor works (clicks register) but the pointer sprite is invisible. The loading/busy cursor appears briefly when launching apps, but the normal `left_ptr` never renders.

### Quick Fix

```bash
export KWIN_FORCE_SW_CURSOR=1
systemctl --user import-environment KWIN_FORCE_SW_CURSOR
systemctl --user restart plasma-kwin_wayland.service   # ⚠️ restarts compositor — screen will flicker
```

### Persistent Fix (survives logout)

Three layers for reliability:

```bash
# Layer A — systemd user env
systemctl --user set-environment KWIN_FORCE_SW_CURSOR=1

# Layer B — environment.d
mkdir -p ~/.config/environment.d
echo 'KWIN_FORCE_SW_CURSOR=1' > ~/.config/environment.d/kwin_sw_cursor.conf

# Layer C — plasma-workspace env sourcing
mkdir -p ~/.config/plasma-workspace/env
cat > ~/.config/plasma-workspace/env/cursor_fix.sh << 'EOF'
#!/usr/bin/env bash
export KWIN_FORCE_SW_CURSOR=1
EOF
chmod +x ~/.config/plasma-workspace/env/cursor_fix.sh

# Also switch to a known-good cursor theme with proper Wayland assets:
plasma-apply-cursortheme Breeze_Light
```

### ⚠️ Pitfall: Restarting KWin on Wayland

**Do NOT restart KWin without warning the user first.** On Wayland, KWin **is the display server**. `systemctl restart plasma-kwin_wayland.service`:

1. KWin stops → compositor dies → screen goes black
2. SDDM (UID 959) grabs the GPU
3. The user session never respawns → **screen stays black permanently**
4. This is expected Wayland behavior, not a crash — but it looks identical to one

**Always ask the user before restarting KWin or any system-disrupting service.**

### Reference

Full diagnosis and additional approaches in `references/invisible-cursor-nvidia-wayland.md`.

## Environment Variables for NVIDIA + Wayland

### Setting on Manjaro/Arch

Check where these are set: `~/.zshrc`, `~/.bashrc`, `~/.profile`, `/etc/environment`

### Recommended Variables

```bash
# Core Wayland
export GBM_BACKEND=nvidia-drm
export GDK_BACKEND=wayland          # GTK apps
export QT_QPA_PLATFORM=wayland      # Qt apps
export MOZ_ENABLE_WAYLAND=1         # Firefox

# NVIDIA driver tuning
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __GL_THREADED_OPTIMIZATIONS=1
export __GL_VRR_ALLOWED=1
export __GL_SYNC_TO_VBLANK=0        # Disable for VRR/tearing

# Hardware video decode
export LIBVA_DRIVER_NAME=nvidia
export NVD_BACKEND=direct

# VA-API
export GBM_BACKEND=nvidia-drm
export __GLX_VENDOR_LIBRARY_NAME=nvidia
```

### GTK4 Renderer Switching

GTK4 uses the `GSK_RENDERER` environment variable to select its scene graph renderer. On NVIDIA Wayland with driver 595.x, the default GL renderer can crash apps in `libnvidia-glcore.so` with a segfault.

**Two confirmed workarounds:**

```bash
# Option A — Force Vulkan renderer (preferred):
export GSK_RENDERER=vulkan

# Option B — Disable GL threaded optimizations (alternative):
export __GL_THREADED_OPTIMIZATIONS=0

# Per-command (for testing):
GSK_RENDERER=vulkan lact gui
__GL_THREADED_OPTIMIZATIONS=0 lact gui

# Both together (most robust):
GSK_RENDERER=vulkan __GL_THREADED_OPTIMIZATIONS=0 lact gui
```

Option A avoids the segfault entirely because Vulkan uses a different code path through the NVIDIA driver. The Vulkan renderer is available in GTK4 4.14+ (tested on 4.22.x).

Option B prevents the NVIDIA GL driver from spawning the worker thread that crashes. Same result, different mechanism. Arch users have also documented this workaround for SIGBUS/SIGSEGV in games on NVIDIA 565.x drivers.

Affected apps include LACT, GNOME Control Center, and other libadwaita/GTK4 applications.

**Desktop entry override for LACT:**
```bash
mkdir -p ~/.local/share/applications
cp /usr/share/applications/io.github.ilya_zlobintsev.LACT.desktop ~/.local/share/applications/
sed -i 's|^Exec=lact gui|Exec=env GSK_RENDERER=vulkan __GL_THREADED_OPTIMIZATIONS=0 lact gui|' ~/.local/share/applications/io.github.ilya_zlobintsev.LACT.desktop
```

### Pitfall Variables

| Variable | Problem | Replace With |
|----------|---------|-------------|
| `__GL_YIELD=USLEEP` | Micro-stutter on modern driver 595+ | Remove or set to `NOTHING` |
| `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1` | Removes KWin NVIDIA smoothness fix | **Remove** — let KWin use default triple buffering |
| `KWIN_TRIPLE_BUFFER=0` | Same as above | Remove |

## System Freeze / "Not Responding" — IRQ Pinning Investigation

### The E-core Trap (NVIDIA on Arrow Lake)

When a user reports *the entire system becomes unresponsive* (not just input lag — full desktop freezes where the cursor stops, clicks don't register, and a hard power cycle is needed), check **CPU IRQ affinity**.

The Intel Core Ultra 7 265K has P-cores (0-7) and E-cores (8-19). Some tuning guides recommend pinning GPU and USB IRQs to dedicated E-cores to "keep P-cores free for games." **This causes system freezes on NVIDIA + Wayland.**

### Why It Breaks

A single E-core handling NVIDIA IRQs can saturate:

```
IRQ 148 (nvidia): 1,027,003 interrupts → ALL on E-core 8
IRQ 146 (nvidia):   563,360 interrupts → ALL on E-core 8
Total: 1.59 million GPU interrupts on one E-core
```

When the user launches a GPU-heavy app (TF2, Dota 2, Chrome WebGL):
- The E-core can't service interrupts fast enough
- KWin compositor can't get GPU interrupt service → desktop freezes
- USB IRQs on other E-cores stall → input stops
- Apps time out and crash (SIGSEGV, SIGTRAP) → orphaned inodes next boot

### The Crash Cascade

```
GPU IRQs pile up on E-core
  → KWin compositor stalls
    → Desktop freezes (cursor stops, input drops)
      → Apps crash uncleanly (dota2 SIGSEGV, Chrome SIGTRAP)
        → Filesystem has orphaned inodes every boot
          → User power-cycles → rapid reboot cluster (4 boots in 90 min)
```

### Diagnostic Commands

```bash
# 1. Check if any IRQ pinning service exists
systemctl status pin-irqs-dynamic 2>/dev/null
ls /usr/local/bin/pin-irqs* 2>/dev/null
ls /etc/systemd/system/pin-irqs* 2>/dev/null

# 2. Read the script to see where IRQs are pinned
cat /usr/local/bin/pin-irqs-dynamic 2>/dev/null

# 3. Check actual IRQ distribution
grep "nvidia" /proc/interrupts | awk '{print $1, $9, $10}' | head -5
# If ALL hits are on E-cores (8-19) and zero on P-cores (0-7), this is the problem

# 4. Check E-core vs P-core max frequencies
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq /sys/devices/system/cpu/cpu8/cpufreq/cpuinfo_max_freq

# 5. Boot history for crash patterns (rapid reboots = freeze signature)
journalctl --list-boots | tail -10

# 6. Check C-state layout on all cores
for cpu in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19; do
    echo -n "CPU $cpu: "
    for s in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*/disable; do
        name=$(cat $(dirname $s)/name 2>/dev/null)
        dis=$(cat $s 2>/dev/null)
        echo -n "$name=$([ "$dis" = 1 ] && echo DIS || echo ON ) "
    done
    echo
done

# 7. C-state latency breakdown (check which states add significant wake delay)
for s in /sys/devices/system/cpu/cpu0/cpuidle/state*; do
    [ -d "$s" ] || continue
    name=$(cat $s/name 2>/dev/null)
    idx=$(cat $s/index 2>/dev/null)
    lat=$(cat $s/latency 2>/dev/null)
    desc=$(cat $s/desc 2>/dev/null)
    echo "State $idx: $name | ${lat}µs wake | $desc"
done
```

### Arrow Lake C-State Layout

On Arrow Lake (Core Ultra 200-series), the ACPI cpuidle system exposes only 4 states — there are **no C6/C7/C8/C9/C10** in cpuidle like older Intel CPUs:

| State | Name | Wake Latency | Description |
|-------|------|-------------|-------------|
| 0 | POLL | 0 µs | Busy-wait (not real idle) |
| 1 | C1_ACPI | 1 µs | MWAIT halt |
| 2 | C2_ACPI | 127 µs | C1E-style enhanced halt |
| 3 | C3_ACPI | **1048 µs** | Deep sleep (package C-state, actual hw C-state managed by PCODE) |

**Pitfall — cpuidle `index` file doesn't exist on kernel 7.x**: When writing scripts to disable C-states, do NOT use `cat "$state_dir"/index` to get the state number. The `index` file is not present on Manjaro/Arch kernel 7.0 and the variable will be empty, causing the `-ge` check to silently skip all states. Extract the index from the directory name instead:

```bash
# ❌ Broken (state_idx is always empty):
state_idx=$(cat "$state_dir"/index 2>/dev/null)

# ✅ Works (extracts number from dir name, e.g. "state2" → "2"):
state_num="${state_dir##*state}"
```

**Key insight**: C3 on Arrow Lake has a **1048 µs** wake penalty. When this is on an IRQ core handling 1.6M+ interrupts, the cumulative delay stalls the compositor. Always disable C2+ on dedicated IRQ cores.

### The Fix — Two Approaches

The user chooses which approach based on their performance/power preference:

**Approach A — GPU+USB on P-cores (fixed template)**
- GPU IRQs → P-cores 0-1 (5.4 GHz, full L2 cache)
- USB IRQs → P-cores 2-3
- Background IRQs → E-cores 12-19
- No C-state changes needed (P-cores already at max)
- Template: `templates/pin-irqs-arrowlake.sh`

**Approach B — GPU+USB on E-cores with C-state disable (alternative)**
Some users prefer keeping P-cores completely free. If so:
- GPU IRQs → E-cores **8-11** (4 cores, round-robin — never 1-2)
- USB IRQs → E-cores **12-13** (separate from GPU, no overlap)
- Background IRQs → E-cores 14-19 (can overlap)
- **Disable C2 and C3** on GPU+USB cores 8-13 (keep only POLL and C1)
- Set `performance` governor on 8-13
- Template: `templates/pin-irqs-arrowlake-ecore.sh`

**Always do this:** Back up the original script first:
```bash
sudo cp /usr/local/bin/pin-irqs-dynamic /usr/local/bin/pin-irqs-dynamic.bak
```

### Verify After Applying

```bash
# Check IRQ distribution
grep "nvidia\\|xhci" /proc/interrupts | awk '{printf "IRQ %s → ", $1; for(i=2;i<=21;i++) if($i>0) printf "CPU%d:%d ", i-2, $i; print ""}'

# Check C-states (should show C2=C3 disabled on GPU+USB cores)
for cpu in 8 9 10 11 12 13; do
  echo -n "CPU $cpu: "
  for s in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*/disable; do
    name=$(cat $(dirname $s)/name 2>/dev/null)
    dis=$(cat $s 2>/dev/null)
    echo -n "$name=$([ "$dis" = 1 ] && echo DIS || echo ON ) "
  done
  echo
done

# Check IRQs are landing on expected cores
grep "nvidia\\|xhci" /proc/interrupts | awk '{print $1, $9, $10, $11, $12, $13}'
```

### Known Limitations

#### NVMe Driver Overrides IRQ Affinity

The NVMe driver does not persistently respect `/proc/irq/*/smp_affinity` writes. After the script sets an NVMe queue's affinity, the driver may reassign it on the next I/O operation. This is a driver-internal MSI-X rebalance, not a script bug.

The straggler catch (Step 5 in the v4 template) re-detects and re-fixes these on every timer tick. Straggler queues typically carry <5% of interrupt volume on GPU/USB cores, so the impact between fixups is negligible.

**Symptoms of NVMe affinity override:**
- IRQ shows `smp_affinity=00300` (CPUs 8-9) despite the script setting it to `fc000`
- Only affects NVMe MSI-X queues; GPU and xHCI IRQs stay pinned correctly

#### EPP Locked by Performance Governor

With `cpufreq.default_governor=performance` in kernel cmdline + `intel_pstate=active`, the `energy_performance_preference` sysfs file is locked by the kernel at boot:

```
/sys/devices/system/cpu/cpu8/cpufreq/energy_performance_preference: Device or resource busy
```

Writing to it (via `echo` or `cpupower -c N set --epp performance`) fails with `EBUSY` even as root. The Intel P-State driver in active mode + performance governor takes exclusive control of the EPP register. The file shows `"default"` as a placeholder — the hardware is managing it internally.

**Cosmetic only.** With `performance` governor + C2/C3 disabled, cores run at max frequency and never enter deep sleep. The EPP value cannot change behavior. The `cpupower` call in the template is included for documentation but will not change the displayed value.

### When To Skip This Check

This only applies to **hybrid CPU architectures** (Intel Core Ultra P/E-core, or soon AMD hybrid). On a traditional CPU where all cores are equivalent, IRQ pinning to any core works fine and this section doesn't apply.

## Input Latency Debugging

### Background GPU Hog Detection

When a user reports mouse/keyboard input lag, the primary cause is often a background app keeping the GPU in high-performance state:

```bash
# 1. Check GPU utilization and clock state
nvidia-smi --query-gpu=utilization.gpu,power.draw,clocks.current.graphics,pstate --format=csv -l 1

# 2. Identify GPU consumers
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

# 3. Check top CPU consumers
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -10

# 4. Check if a game is running in background
# TF2: tf_linux64, Dota2: dota2, etc.

# 5. IO wait
top -bn1 | head -5
```

Common culprits: Team Fortress 2, Dota 2, other Source engine games running in background. Kill with `kill <pid>` or suspend with `kill -STOP <pid>`.

## System Log Sweep Checklist

```bash
# Failed systemd services
systemctl --failed
systemctl --user --failed

# Core dumps
coredumpctl list --no-legend 2>/dev/null | tail -10

# ACPI errors
journalctl -b --no-hostname | grep -iE "acpi.*error|acpi.*fail"

# PCIe/disk errors
journalctl -b --no-hostname | grep -iE "pcie.*error|nvme.*error|i/o error|critical medium"

# USB errors
journalctl -b --no-hostname | grep -iE "usb.*error|xhci.*error"

# Orphaned inodes (filesystem issues at boot)
journalctl -b --no-hostname | grep -i "clearing orphaned"

# PowerDevil restarts
journalctl -b --no-hostname | grep -i "org_kde_powerdevil" | grep -c "Time since library initialized"
```

## KWin Compositor Settings

Check via `~/.config/kwinrc`:

```ini
[Compositing]
AllowTearing=true               # For VRR/gsync-compatible monitors
AnimationSpeed=1
Enabled=true
LatencyPolicy=LatencyLow        # Reduce compositor latency
UnredirectFullscreen=true       # Direct scanout for games
VrrPolicy=Never                 # "Never" or "FullscreenOnly" safest on NVIDIA
```

### Pitfall: KWIN_DRM_NO_ATOMIC

Do NOT set `KWIN_DRM_NO_ATOMIC=1` to work around DPMS wake failures. This forces KWin to use legacy modesetting, which **breaks explicit sync** on NVIDIA Wayland. Explicit sync (driver 555+/KWin 6.1+) requires atomic KMS. Breaking it causes stutter and tearing that's worse than the DPMS problem. Use the GSP firmware fixes in this skill instead.

## Autostart Fix Pattern

When a user has a shell script in `~/.config/autostart/`, KDE's autostart system requires `.desktop` files. A bare `.sh` file generates:
```
Invalid section header '[ -z "$EVENT" ] && exit 0'
```

**Fix:**
```bash
mkdir -p ~/.local/bin
mv ~/.config/autostart/script.sh ~/.local/bin/script.sh
chmod +x ~/.local/bin/script.sh
```

Create `~/.config/autostart/script.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Descriptive Name
Exec=/home/user/.local/bin/script.sh
Terminal=false
X-KDE-autostart-phase=2
StartupNotify=false
```

## DLSS Upgrade via DLL Direct Replacement

### User Preference Note

This user communicates in extreme shorthand — fragment questions like "a sa", "f aa using", "asa are you a sure", "a also". They want:
- **Commands first, explanation never** — give the exact command immediately. Do not explain why something is broken. Do not theorycraft. When they ask a yes/no question, answer it and stop.
- **Direct replacement over proxy** — when presented with a choice between a proxy/middleware approach (OptiScaler) and direct file replacement (swap nvngx_dlss.dll), they explicitly chose the simpler path. Lead with direct replacement first; only suggest OptiScaler or other proxy layers if direct replacement doesn't work.
- **Automated, not manual** — if a fix needs repeating (DLSS updates), write a script and set up cron/launch hooks. They will not revisit a manual process.
- **No clarifying questions** — list all options in one message. Let them choose. Do NOT ask "which approach do you prefer" — list them and wait.
- **ASK before disruptive actions** — never restart KWin, the display manager, or any compositor/service without explicit user permission. Restarting the compositor on Wayland kills the session. Ask first.

### The Problem

`PROTON_DLSS_UPGRADE=1` is registered as a compat_config flag in GE-Proton but the actual download/setup code in `protonfixes/upscalers.py` is **never called from the main proton script**. The specific root cause: `setup_upscalers()` is defined in `protonfixes/upscalers.py` (300+ lines of DLSS/XeSS/FSR download logic) but no invocation of it exists in the main `proton` bootstrap path. The env var passes `check_environment()`, adds "dlss" to `compat_config`, and then nothing happens. The flag does nothing — no DLL gets downloaded, no upgrade happens.

### The Fix — Manual DLSS DLL Replacement

Replace the game's `nvngx_dlss.dll` (old version, ~14MB) with the latest DLSS 310.7.0.0 (~57MB) directly in the game directory.

**Find the latest DLSS version:**

The GE-Proton upscaler manifest at `https://loathingkernel.github.io/proton-upscalers/manifest.json` lists all available DLSS versions. The `dlss` key has versions sorted oldest-first. Filter out `is_dev_file` entries and sort by `version_number` descending to find the latest:

```python
import json, urllib.request
url = 'https://loathingkernel.github.io/proton-upscalers/manifest.json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as f:
    manifest = json.loads(f.read())
dlss = sorted(
    [d for d in manifest['dlss'] if not d.get('is_dev_file')],
    key=lambda x: x.get('version_number', 0), reverse=True
)
latest = dlss[0]
print(f"Latest DLSS SR: {latest['version']}")
print(f"Download URL: {latest['download_url']}")
```

**Three DLLs needed for a full upgrade:**

| DLL | Purpose | Manifest Key |
|-----|---------|--------------|
| `nvngx_dlss.dll` | Super Resolution (main upscaler) | `dlss` |
| `nvngx_dlssg.dll` | Frame Generation | `dlss_g` |
| `nvngx_dlssd.dll` | Depth / Denoiser | `dlss_d` |

Download each (the manifest stores `.xz` compressed files — decompress with `lzma` after download), then drop into the game directory:

```bash
install -m644 nvngx_dlss.dll "/path/to/Diablo II Resurrected/nvngx_dlss.dll"
install -m644 nvngx_dlssg.dll "/path/to/Diablo II Resurrected/nvngx_dlssg.dll"
install -m644 nvngx_dlssd.dll "/path/to/Diablo II Resurrected/nvngx_dlssd.dll"
```

The game loads the local DLL over the bundled one. No Wine DLL override needed for `nvngx_dlss.dll` — the game's own loader picks it up from the same directory.

### Auto-Update Script

`scripts/d2r-dlss-update.py` automates the direct replacement process. It:

1. Fetches the GE-Proton upscaler manifest
2. Finds the latest non-dev DLSS SR / FG / Depth DLLs
3. Compares file sizes with what's installed — replaces if newer
4. Backs up old DLLs to `/tmp/d2r-dlss-backups/`

**Usage:**
```bash
python3 scripts/d2r-dlss-update.py "/path/to/Diablo II Resurrected"
```

**Steam launch options pattern (runs before game starts):**
```bash
python3 /path/to/d2r-dlss-update.py "/path/to/game" && mangohud %command%
```

**Weekly cron pattern:**
```bash
0 10 * * 1 python3 /path/to/d2r-dlss-update.py "/path/to/game"
```

The script works for any game with DLSS, not just D2R — just point it at the game's directory.

### Verifying the Upgrade

In-game check:
- Enable DLSS in graphics settings
- The newer DLSS DLL provides different quality presets (K = newest transformer model)
- Press Insert in the OptiScaler overlay (if installed) to see what DLSS version is loaded

### ⚠️ DLSS Indicator (`PROTON_DLSS_INDICATOR=1`) Limitation

`PROTON_DLSS_INDICATOR=1` does NOT produce a visible on-screen overlay with the DLSS 310.x release DLLs. Despite GE-Proton correctly setting `DXVK_NVAPI_SET_NGX_DEBUG_OPTIONS=DLSSIndicator=1024,DLSSGIndicator=2,` and DXVK-NVAPI writing `ShowDlssIndicator=1024` to the NGX registry key at `SOFTWARE\NVIDIA Corporation\Global\NGXCore`, the standard-release DLSS DLL doesn't render a visual indicator — the debug output goes to a log/console channel, not the screen. The visual green "DLSS" indicator on Windows requires NVIDIA Profile Inspector or a debug build of the DLSS DLL.

To verify DLAA is active, compare GPU usage at the same FPS cap:
- DLSS Quality (66% scale) → lower GPU usage
- DLAA/ultra_quality (100% native) → noticeably higher GPU usage at same FPS

### DLAA Forcing via DXVK-NVAPI DRS Settings

DLAA is DLSS at native resolution — the DLSS neural network applies temporal anti-aliasing without the upscaling step. It produces the best image quality at the cost of rendering full-res.

D2R (and other DLSS-capable games) don't expose a DLAA toggle in their menu. But with the DLSS 310.7.0.0 DLL installed, the render preset system includes an `ultra_quality` preset that is effectively DLAA: native render resolution + maximum quality + no upscaling.

**How it works:** DXVK-NVAPI intercepts the game's queries to the NVIDIA driver's DRS (Driver Settings) system. The `DXVK_NVAPI_DRS_SETTINGS` env var overrides specific driver setting IDs. DXVK-NVAPI parses `key=value` pairs and returns the override when the game or DLSS DLL queries that setting:

```
nvapi_drs.cpp: Reads DXVK_NVAPI_DRS_SETTINGS env var
  → parses "key=value" into {setting_id: value} map
    → on NvAPI_DRS_GetSetting(), returns map value if key matches
      → DLSS DLL requests "ngx_dlss_sr_override_render_preset_selection"
        → DXVK-NVAPI returns "ultra_quality" → DLSS renders native res (DLAA)
```

**Note on value names:** The values are symbolic names interpreted by the DLSS DLL itself. DXVK-NVAPI's DRS parser (`nvapi_drs.cpp`) treats the value as a generic DWORD — the actual numeric mapping from names like `ultra_quality` to the DLSS render preset is done inside the NVIDIA DLSS DLL, not in DXVK-NVAPI. So the valid value names depend on what the installed DLSS DLL recognizes.

**The launch option to force DLAA:**

```
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=ultra_quality" mangohud %command%
```

**How to use:**
1. Set DLSS to **Quality** in the game's graphics menu (this keeps the DLSS pipeline active)
2. Add the DRS override above to the Steam launch options
3. The DLSS 310.7.0.0 DLL receives the override and renders at native resolution with full temporal AA — no upscaling, just anti-aliasing

**The concept of "forcing" vs "selecting":** The game's menu lacks a DLAA option. The `ngx_dlss_sr_override` flag tells DXVK-NVAPI to intercept ALL DLSS SR calls and apply the override. The game thinks it's running DLSS Quality (which keeps the DLSS pipeline alive — some games disable DLSS entirely if the preset doesn't match a known menu option) but the DLL actually runs in ultra_quality (DLAA) mode.

**Important:** The `ngx_dlss_sr_override=on` flag MUST be present whenever any `ngx_dlss_sr_override_render_preset_selection` is set. Without the override flag, the render preset selection is ignored because the game's original preset is used.

### DLSS / Upscaler Upgrade via OptiScaler

### What OptiScaler Does

[OptiScaler](https://github.com/optiscaler/OptiScaler) is a middleware DLL that intercepts upscaler API calls from the game (DLSS, FSR, XeSS inputs) and redirects them to a chosen backend. It acts as a proxy that can:
- Replace DLSS with FSR/XeSS or vice versa
- Upgrade DLSS version (DLSS 3.x → 4.x/5.x) by acting as the proxy
- Add frame generation via OptiFG
- Override mip bias, sharpness, anisotropy

### Known Limitations for D2R

From the [OptiScaler issue tracker](https://github.com/optiscaler/OptiScaler/issues/323) (closed as "not planned"):
- Mip bias override doesn't take effect in D2R — the game's render pipeline bypasses OptiScaler's shader hooks
- Some users report OptiScaler not hooking at all with D2R (July 2025 discussion)
- The game uses a nonstandard DX12 renderer that intercepts upscaler calls at a different layer

Despite these issues, the DLSS DLL direct replacement (above) is more reliable for D2R specifically. OptiScaler is worth trying for games where the native upscaler pipeline is standard DX12.

### Installation (for games where it works)

```bash
# 1. Download OptiScaler latest release
curl -sL https://api.github.com/repos/optiscaler/OptiScaler/releases/latest | grep browser_download_url

# 2. Extract to game directory
7z x Optiscaler_*.7z -o"/path/to/game/dir"

# 3. Rename OptiScaler.dll to the proxy DLL name for DX12 games
cp OptiScaler.dll dxgi.dll     # For DX12 games (most common)
# OR: cp OptiScaler.dll version.dll   # Alternative proxy name

# 4. Configure OptiScaler.ini for your GPU
# For NVIDIA with DLSS:
Dx12Upscaler=dlss
DlssPresetOverride=true

# 5. Steam launch options
PROTON_USE_OPTISCALER=1 WINEDLLOVERRIDES="dxgi=n,b" mangohud %command%
```

`PROTON_USE_OPTISCALER=1` adds "optiscaler" to GE-Proton's compat_config. `WINEDLLOVERRIDES="dxgi=n,b"` ensures the native DLL (OptiScaler renamed) loads before Wine's builtin.

### OptiScaler's vulkan_present_mode for Latency Control

When OptiScaler is active, setting `vulkan_present_mode` in the MangoHud config (not OptiScaler.ini) overrides the game's present mode at the Vulkan layer:

| Mode | Latency | Tearing | Use Case |
|------|---------|---------|----------|
| `immediate` | Lowest | Yes | Competitive, every ms counts |
| `mailbox` | Low | No | Best all-rounder |
| `fifo` | Highest | No | V-Sync on, avoid |
| `fifo_relaxed` | Medium | Sometimes | V-Sync that breaks under load |

For D2R: `mailbox` gives low latency without tearing. When used with MangoHud's `fps_limit`, the cap handles frame pacing so separate V-Sync isn't needed.

## Proton Game Settings Troubleshooting (NVIDIA Wayland)

### User Interaction Style

This user communicates in extreme shorthand — fragment questions like "a sa", "f aa using", "asa are you a sure", "a also". They want:
- **Commands first, explanation never** — give the exact command immediately. Do not explain why something is broken. Do not theorycraft. When they ask a yes/no question, answer it and stop.
- **Direct replacement over proxy** — when given a choice between a proxy/middleware approach (OptiScaler) and direct file replacement (swap nvngx_dlss.dll), they choose direct. Always lead with the simplest path first.
- **Automated, not manual** — if a fix needs repeating (DLSS updates), write a script and set up cron/launch hooks. They will not revisit a manual process.
- **No clarifying questions** — list all options in one message. Let them choose. Do NOT ask "which approach do you prefer" — list them and wait.

### The Core Problem

NVIDIA + Wayland introduces a presentation-layer gap that breaks two common gaming features:
1. **In-game graphics settings not persisting** — fullscreen mode, resolution, vsync, and quality presets may not save across sessions or may not take effect at all.
2. **In-game frame limiter not working** — the game's FPS cap relies on DirectX presentation timing through DXVK/VKD3D that doesn't translate properly under Wayland.

Both issues are specific to the NVIDIA + Wayland + Proton stack, not the game itself.

### Root Cause: In-Game Frame Limiter Cannot Function on NVIDIA Wayland

The in-game frame limiter (stored as `Framerate Cap` in `Settings.json`) is a **CPU-sleep-based** timer. The game engine calculates the sleep duration needed to hit the target FPS, then calls `Sleep()` between `IDXGISwapChain::Present()` calls.

Under VKD3D-Proton (for DX12 games like D2R Infernal Edition), this breaks for three independent reasons:

1. **Wine Sleep timers are imprecise** — Wine's `Sleep()` doesn't have the same high-resolution timer guarantees as Windows. The game undersleeps or oversleeps by a variable margin.

2. **VKD3D swapchain buffering decouples frame timing** — The game thread sleeps, but VKD3D-Proton's internal Vulkan swapchain has its own pacing. The GPU continues rendering at full speed through the swapchain queue. The game *thinks* it's limiting to 60fps, but VKD3D is still presenting at uncapped speed.

3. **Wayland + NVIDIA proprietary driver adds another indirection** — Wayland's `wl_surface::commit` + `fifo`/`immediate` present modes don't expose the same vsync control to the Vulkan layer that X11's `PresentPixmap` does. The NVIDIA driver handles frame presentation in kernel mode, bypassing the game's sleep timers entirely.

Source: VKD3D-Proton maintainer Hans-Kristian (issue #1377): *"If you have a CPU fps limiter that's below vsync rate, the problem with that approach is horrible frame pacing usually"* and *"Disabling vsync makes all of this somewhat moot — we use fallback paths to pump latency fences when vsync is disabled."*

**There is no Proton env var, no Wine tweak, no VKD3D config that makes a CPU sleep-based frame limiter work correctly.** The game's approach is fundamentally incompatible with how VKD3D-Proton + Vulkan + Wayland + NVIDIA present frames. MangoHud (Vulkan-layer cap) or Gamescope (compositor-level cap) are the only reliable approaches.

The full D2R `Settings.json` structure (proton prefix path for D2R Infernal Edition):

| Field | Value Meaning |
|-------|-------------|
| `VSync` | 0=off, 1=on |
| `Framerate Cap` | Integer FPS limit (0=unlimited) |
| `Framerate Target` | 0=not set |
| `NVIDIA DLSS` | 0=off, 1=Quality, 2=Balanced, 3=Performance, 4=Ultra Performance |

Settings file location (Windows path within prefix):
```
drive_c/users/steamuser/Saved Games/Diablo II Resurrected/Settings.json
```

Actual absolute path on Arch/Manjaro:
```bash
~/.local/share/Steam/steamapps/compatdata/2536520/pfx/drive_c/users/steamuser/Saved Games/Diablo II Resurrected/Settings.json
```

### First-Try Fix: Disable Wayland Native Mode

The single most reliable first step for any game with settings/framerate issues:

```
PROTON_ENABLE_WAYLAND=0 %command%
```

This forces the game to run through XWayland instead of Proton's Wayland driver. The X11 presentation path through DXVK/VKD3D handles fullscreen, resolution changes, and frame timing correctly on NVIDIA. Multiple ProtonDB reports confirm this fixes the "stuck in windowed mode" and "frame limiter ignored" symptoms.

### Frame Limiter: In-Game vs MangoHud

The in-game frame limiter is fundamentally broken on NVIDIA Wayland — see "Root Cause" above. Do NOT suggest tweaks to make the in-game limiter work; it cannot.

**MangoHud** is the correct replacement — it hooks at the Vulkan layer, below the game's own timer:

```bash
# Install
sudo pacman -S mangohud

# Config file: ~/.config/MangoHud/MangoHud.conf
fps_limit=60           # Or your target FPS
no_display=1           # Hides the overlay — silent cap

# Steam launch option
mangohud %command%
```

**Gamescope** is an alternative — it provides a compositor-level hard cap:

```bash
sudo pacman -S gamescope

# Steam launch option
gamescope -f -r 60 -- %command%    # -r 60 = hard cap at 60 FPS
```

### GE-Proton vs Stock Proton

When a game's display settings don't work with the default Proton version, try:

1. **Proton Experimental** — often has the newest NVIDIA Wayland fixes
2. **GE-Proton (latest)** — GloriousEggroll's builds include community patches ahead of Valve's releases. On NVIDIA+Wayland, GE-Proton10-34 or newer is known to fix fullscreen/resolution issues when stock Proton 10 fails.
3. **Proton 9.x or older** — if Experimental and GE both fail, a known-stable older version can be a last resort

Install/upgrade GE-Proton:
```bash
protonup -d ~/.local/share/Steam/compatibilitytools.d/
```

### Alt+Enter Band-Aid

For the "stuck in fixed window" or "1/4 screen only renders" bugs (common on NVIDIA + Proton 10):

1. Launch the game
2. Hit **Alt+Enter** (switches to windowed)
3. Hit **Alt+Enter** again (switches back to fullscreen)

This fixes the render buffer issue and resolution lock until next launch.

### Battle.net / ClientSDK Fix

Blizzard games (D2R, WoW, Overwatch) running through Proton need a specific folder for the Battle.net login system:

```bash
mkdir -p "/path/to/proton/prefix/pfx/drive_c/users/steamuser/AppData/Local/Blizzard Entertainment/ClientSdk"
```

Without it, the game shows "You have not been online in the last 30 days" even when online. The exact path depends on the game's Steam compatdata ID — for D2R Infernal Edition on Steam it's:

```bash
mkdir -p ~/.local/share/Steam/steamapps/compatdata/2536520/pfx/drive_c/users/steamuser/AppData/Local/Blizzard Entertainment/ClientSdk
```

### Vsync Behavior

On NVIDIA Wayland, in-game vsync can cause instability (FPS drops, frame pacing issues). If a game has unusual performance problems, try turning vsync OFF in-game and let KWin's compositor handle frame presentation. One ProtonDB report on D2R: "If you have weird FPS drops or overall lower FPS than expected turn off the Vsync — for some reason it makes the game less stable."

### Reference

- `references/proton-d2r-nvidia-wayland.md` — Diablo 2 Resurrected-specific: ProtonDB findings, launch options, settings debugging, and frame limiter fixes.

## HDR Gaming — gamescope + Proton on NVIDIA Wayland

### Overview

HDR gaming on Linux works through a stack: **gamescope** (micro-compositor) presents an HDR surface → **VKD3D-Proton** (DX12) or **DXVK** (DX11) exposes HDR metadata to the game → **KWin** composits to the display. On NVIDIA Wayland, all three layers must cooperate.

**Prerequisites** (check with `kscreen-doctor -o | grep HDR`):

| Layer | Minimum Version | Check |
|-------|----------------|-------|
| KDE Plasma | 6.0+ (KWin with HDR infrastructure) | `plasmashell --version` |
| NVIDIA driver | 545.29+ (explicit sync), 595+ recommended | `nvidia-smi --query-gpu=driver_version --format=csv,noheader` |
| gamescope | 3.14+ (HDR support) | `pacman -Q gamescope` |
| Proton GE | GE-Proton10+ (VKD3D 2.14+ HDR) | `ls ~/.local/share/Steam/compatibilitytools.d/` |

### Step-by-step

**1. Enable HDR in KDE**

GUI: System Settings → Display → HDR → On

CLI (match your output name from `kscreen-doctor -o`):
```bash
kscreen-doctor output.DP-3.hdr.enable
```

Verify:
```bash
kscreen-doctor -o | grep -A5 "HDR: enabled"
```

**2. Verify the monitor reports HDR EDID**

```bash
for c in /sys/class/drm/card0-*/edid; do
  conn=$(basename $(dirname $c))
  hdr=$(strings $c 2>/dev/null | grep -c -iE "hdr|HDR")
  [ "$hdr" -gt 0 ] && echo "$conn: HDR-capable"
done
```

If empty, the monitor doesn't advertise HDR via EDID — gamescope's `--hdr-itm-enable` (inverse tone mapping) can force SDR→HDR conversion.

**3. Install gamescope (Manjaro/Arch)**
```bash
sudo pacman -S gamescope
```

**4. Set Proton version for the game**

Steam → Game → Properties → Compatibility → Force a specific Steam Play tool → **GE-Proton11-1** (or latest GE-Proton).

Check installed versions:
```bash
ls ~/.local/share/Steam/compatibilitytools.d/
```

Install/upgrade via ProtonUp-Qt:
```bash
protonup-qt
```
Or CLI:
```bash
protonup -d ~/.local/share/Steam/compatibilitytools.d/
```

**5. Steam launch options — gamescope HDR**

```bash
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- %command%
```

Flags:

| Flag | Purpose |
|------|---------|
| `-W 3440 -H 1440` | Output resolution (match your monitor) |
| `-r 165` | Refresh rate |
| `--hdr-enabled` | Enable HDR output from gamescope |
| `--adaptive-sync` | VRR / G-Sync passthrough |
| `--steam` | Steam integration mode |
| `--hdr-itm-enable` | Inverse tone mapping — forces SDR→HDR when game doesn't output native HDR |

**6. NVIDIA-specific env vars (if HDR doesn't trigger in-game)**

```bash
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- env PROTON_ENABLE_NVAPI=1 PROTON_HIDE_NVIDIA_GPU=0 VKD3D_CONFIG=hdr %command%
```

- `VKD3D_CONFIG=hdr` — tells VKD3D-Proton (DX12) to advertise HDR. For Dead Space Remake, Cyberpunk 2077, etc.
- `DXVK_HDR=1` — for DXVK (DX11) games, not VKD3D
- `PROTON_ENABLE_NVAPI=1` — enables DLSS / Reflex via NVAPI

**7. In-game Settings**

Settings → Display → **HDR: On**. Adjust peak brightness to match monitor (check via `kscreen-doctor -o` → "Peak brightness: X nits").

### Troubleshooting

**HDR toggle missing in-game or greyed out**
```bash
# Confirm gamescope running in HDR mode
cat /proc/$(pidof gamescope)/cmdline 2>/dev/null | tr '\0' ' '
# Re-enable if KDE lost HDR after sleep
kscreen-doctor output.DP-3.hdr.enable
# Try VKD3D_CONFIG=hdr for DX12 games
```

**Black screen with gamescope**
Remove `--adaptive-sync` — some NVIDIA + monitor combos fail with VRR + HDR together.

**HDR looks washed out**
Match game's peak brightness setting to monitor (from `kscreen-doctor -o | grep "peak brightness"`). Use `--hdr-itm-enable` for monitors without HDR EDID.

**Proton GE not showing in Steam dropdown**
```bash
steam --shutdown && steam
```

**DX11 game (DXVK instead of VKD3D)**
```bash
gamescope -W 3440 -H 1440 -r 165 --hdr-enabled --adaptive-sync --steam -- env DXVK_HDR=1 %command%
```

DXVK (DX9-11) and VKD3D-Proton (DX12) use different HDR env vars. Check which renderer on protondb.com.

### Reference

- `references/hdr-gaming-setup.md` — session-specific: Dead Space Remake on Manjaro KDE Wayland NVIDIA, gamescope launch options, Proton GE selection, and verification commands.

## Linked Files in This Skill

| File | Type | Purpose |
|------|------|---------|
| `references/nvidia-drm-syncobj-fd-leak.md` | Reference | nvidia-open DRM syncobj FD leak causing plasmashell crash — diagnostic, quick fix, permanent fix |
| `references/chrome-gpu-research.md` | Reference | Research notes on Chrome GPU + NVIDIA Wayland |
| `references/powerdevil-dpms-failure.md` | Reference | DPMS display wake failure analysis |
| `references/irq-pinning-freezes.md` | Reference | IRQ pinning on E-cores causing system freezes, including C-state analysis |
| `references/scx-sched-ext-config.md` | Reference | scx_rustland/scx_loader config pitfalls and mode cases |
| `references/gtk4-gl-crash-nvidia-wayland.md` | Reference | GTK4/libadwaita app crash in libnvidia-glcore.so on NVIDIA Wayland — LACT case study and `GSK_RENDERER=vulkan` fix |
| `references/nvidia-r610-driver-release.md` | Reference | NVIDIA 610.43.02 driver release notes — DRM color pipeline, Vulkan fixes, FP16 Wayland, Xinerama removal, Blackwell GSP status, PCIe Gen 5 diagnostic |
| `references/nvidia-open-vs-dkms-blackwell.md` | Reference | nvidia-open vs nvidia-dkms for Blackwell RTX 50-series — module requirements, GSP implications, and known issues |
| `references/nvidia-open-vs-dkms-blackwell.md` | Reference | nvidia-open vs nvidia-dkms for Blackwell RTX 50-series — module requirements, GSP implications, and known issues |
| `references/nvidia-suspend-resume-execcondition.md` | Reference | NVIDIA 595+ module license changed to "Dual MIT/GPL" — suspend/resume services skipped, black screen after wake, systemd drop-in override fix |
| `references/invisible-cursor-nvidia-wayland.md` | Reference | Invisible cursor on NVIDIA Wayland — KWIN_FORCE_SW_CURSOR fix, cursor theme switching, xcb-cursor check, KWin restart pitfalls |
| `references/proton-d2r-nvidia-wayland.md` | Reference | D2R-specific: ProtonDB findings, launch options, settings debugging, and frame limiter fixes for NVIDIA Wayland |
| `references/chrome-archwiki-flags-research.md` | Reference | Chrome flag configuration from ArchWiki — tested configs, pitfall matrix, and authoritative documentation for NVIDIA + Wayland |
| `scripts/check-irq-pinning.sh` | Script | Quick diagnostic: verify IRQ distribution + C-state + governor status after applying pinning template. Exit codes: 0=healthy, 1=warnings, 2=errors. |
| `scripts/d2r-dlss-update.py` | Script | Auto-update any game's DLSS DLLs to the latest version from the GE-Proton manifest. Usage: `python3 scripts/d2r-dlss-update.py /path/to/game` |
| `templates/pin-irqs-arrowlake.sh` | Template | Fixed IRQ pinning script (GPU+USB → P-cores) |
| `templates/pin-irqs-arrowlake-ecore.sh` | Template | Alternative IRQ pinning (GPU+USB → E-cores with C-state disable) |
