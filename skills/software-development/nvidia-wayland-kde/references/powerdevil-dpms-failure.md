# KDE PowerDevil + DPMS on NVIDIA Wayland — Research Notes

## The Core Problem

`Watching for DPMS state changes unimplemented` — KDE PowerDevil cannot monitor display power state on NVIDIA + Wayland. This is an integration gap between the NVIDIA proprietary driver and KDE's power management infrastructure.

## Symptoms

1. Display blanks after idle timeout → monitor stays black on keypress/mouse move
2. Keyboard backlight flashes briefly (USB resumes) but screen stays dark
3. PowerDevil crashes and restarts repeatedly (different PIDs in logs)
4. `Failed to register with host portal — app info not found` accompanies the DPMS warning
5. `no kernel backlight interface found` — HP X34 and other DDC/CI monitors don't have a kernel backlight sysfs

## Chain of Failure

```
Input event → USB subsystem resumes (KB backlight on) → KWin detects input
→ PowerDevil tries DPMS unblank → DPMS monitoring is broken → DRM modeset fails
→ Display stays black → KB backlight times out → User presses key again → loop
```

## An Easily Missed Amplifier: IgnoreIdleInhibitors

In `~/.config/powerdevilrc`:
```ini
[General]
IgnoreIdleInhibitors=true

[Inhibitions]
BlockedInhibitions=steam:Playing a game,...
```

This causes the system to ignore "don't sleep" signals from Steam, Chrome (video/audio), GameMode, etc. Combined with `TurnOffDisplayIdleTimeoutSec=300` and `AutoSuspendIdleTimeoutSec=3600`, the system will:
- Blank display after 5 min even while gaming
- Attempt suspend after 1 hour even while gaming

## GSP Firmware as Root Cause of DPMS Wake Failures

On RTX 40/50 series (Ada/Blackwell), the NVIDIA GSP firmware handles DisplayPort link training for DPMS wake. It has a known bug where this handshake fails on certain monitors (HP X34, Dell S-series) — black screen after display-off while USB devices respond normally.

Two fixes in the main SKILL.md "GSP Firmware" section:
- **Option A** — RMUseSwLinkTraining=1 (targeted, keep error recovery)
- **Option B** — NVreg_EnableGpuFirmware=0 (complete, removes error recovery)

GSP link training failures are silent (no Xid errors logged). Apply via:
```bash
sudo sed -i 's/NVreg_RegistryDwords="\\(.*\\)"/NVreg_RegistryDwords="\\1;RMUseSwLinkTraining=1"/' /etc/modprobe.d/nvidia-perf.conf
```

If both options are applied, RMUseSwLinkTraining is redundant (GSP bypassed). Clean duplicates.

## Fix Verification

After applying fixes, confirm:
```bash
# PowerDevil no longer restarting
journalctl -b --no-hostname | grep "org_kde_powerdevil" | grep "Time since library initialized" | wc -l
# Should be 1 (or very few, just the boot instance)

# Configs are correct
grep -A5 "SuspendAndShutdown" ~/.config/powermanagementprofilesrc
grep -A5 "Display" ~/.config/powerdevilrc
```
