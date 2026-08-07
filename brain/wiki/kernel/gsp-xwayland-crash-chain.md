---
source_session: "20260603_234459_ebf65d"
date: 2026-07-11
category: kernel
related: [pin-irqs-dynamic-v4, nvidia-gsp-firmware]
---

# GSP → Xwayland Crash → 100% CPU Loop Chain

A crash chain where NVIDIA GSP firmware instability cascades into desktop application meltdown.

## Timeline

1. **GSP firmware crashes** — causes a GPU channel timeout or driver error
2. **Xwayland dies** — kernel log shows `(EE) failed to write to Xwayland fd: Broken pipe`
3. **Wayland compositor (KWin) restarts** — all Wayland-connected apps lose their connection
4. **systemsettings and elisa don't recover** — they enter a fallback: `There are no outputs — creating placeholder screen`
5. **Infinite render loop** — both apps try to paint onto a dead/placeholder output, burning **~100% CPU continuously**

## Impact

- systemsettings burned **14h 59min CPU in 15h 3min wall time** (99.6% utilization for 15 hours straight)
- elisa similarly affected
- System becomes sluggish as two CPU cores are fully saturated

## Fix

- Disable GSP firmware: `NVreg_EnableGpuFirmware=0` in `/etc/modprobe.d/nvidia-perf.conf`
- Rebuild initramfs: `sudo mkinitcpio -P` then reboot
- Emergency kill if happens before reboot: `killall systemsettings elisa`

## Related

- [[pin-irqs-dynamic-v4]] — companion script for system tuning
- [[nvidia-gsp-firmware]] — broader GSP issues
