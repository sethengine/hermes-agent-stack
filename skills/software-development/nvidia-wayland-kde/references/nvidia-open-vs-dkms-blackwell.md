# nvidia-open vs nvidia-dkms for Blackwell (RTX 50-Series)

## Quick Answer

**Blackwell GPUs (RTX 5060 Ti, 5070, 5080, 5090) require nvidia-open.** The proprietary nvidia-dkms module does not support Blackwell at all. There is no choice.

## Why

### nvidia-open (Open Kernel Module)

- Open-source kernel module (GPL/MIT licensed) for the proprietary NVIDIA userspace driver
- Contains the kernel-mode driver; proprietary GSP firmware + userspace libraries handle the rest
- Required for Turing (RTX 20-series) and newer, **mandatory for Blackwell**
- GSP firmware **cannot be disabled** — this is by design, as GSP offloads proprietary code into a firmware blob, enabling the kernel module itself to be open source

### nvidia-dkms (Proprietary Kernel Module)

- Traditional closed-source kernel module NVIDIA shipped for decades
- Supports Maxwell (GTX 900) through Lovelace (RTX 40-series)
- **Does not support Blackwell at all**
- GSP firmware can be disabled with `NVreg_EnableGpuFirmware=0` (still works on this module for pre-Blackwell GPUs)

## GSP Firmware — The Critical Difference

| Aspect | nvidia-dkms (Proprietary) | nvidia-open |
|--------|--------------------------|-------------|
| GSP can be disabled? | **Yes** — `NVreg_EnableGpuFirmware=0` | **Yes*** — same parameter works, but requires initramfs rebuild |
| Why GSP exists | Optional — firmware for RISC-V co-processor | **Architectural requirement** — proprietary code lives in firmware blob so kernel module is open |

**\*Correction — GSP CAN be disabled on nvidia-open.** Setting `NVreg_EnableGpuFirmware=0` in `/etc/modprobe.d/nvidia*.conf` works on both module types. The difference is that nvidia-open modules load **from initramfs** (early boot via mkinitcpio), so the modprobe config file on the root filesystem is NOT read unless the initramfs includes it. The fix:

```bash
sudo mkinitcpio -P   # rebuild initramfs to bake in modprobe params
sudo reboot
```

On Arch/Manjaro with the `modconf` hook in `/etc/mkinitcpio.conf`, modprobe.d files ARE included in the initramfs by default. The key is that the initramfs must be rebuilt AFTER changing the modprobe config entry.

Without an initramfs rebuild, `nvidia-smi --query-gpu=gsp.mode.current --format=csv` will still show `Enabled` even though the modprobe config has `NVreg_EnableGpuFirmware=0` — the module loaded with GSP enabled from the old initramfs snapshot and never re-read the root filesystem config.
| Known GSP issues | Stutter on KDE Wayland (high refresh), crashes on some laptops | Same issues, but **cannot be worked around** by disabling GSP |
| Arch default | Legacy (replaced by nvidia-open) | Default since R590 transition |
| 595.71.05 crash | N/A (doesn't support Blackwell) | Known RTX 5060 Ti GSP crash — black screen, 100% fans, hard reset (CachyOS forum) |

## Architecture

nvidia-open is NOT a fully open-source driver. It's a hybrid:

```
User:     nvidia-open-dkms (kernel module, GPL/MIT, source visible)
Firmware: GSP firmware blob (proprietary, loaded onto GPU RISC-V processor)
Ring-0:   nvidia.ko (proprietary, handles RM API, memory management)
```

The GSP firmware handles DisplayPort link training, engine error recovery (Xid 13/32 auto-recovery), power management, and GPU scheduling. Without it, the open kernel module can't function.

## Performance

Per [GitHub discussion #680](https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/680) and [r/archlinux](https://www.reddit.com/r/archlinux/comments/1pt9bwi/is_there_a_difference_between_nvidiadkms_and/):

- **Performance is comparable** between nvidia-open and nvidia-dkms on the same hardware
- The real difference is **GSP firmware behavior**, not the kernel module code path
- nvidia-open + GSP enabled ≈ nvidia-dkms + GSP enabled in benchmarks
- nvidia-dkms + GSP disabled can be more stable (no GSP crashes) but loses engine error recovery
- On Blackwell, GSP cannot be disabled regardless, so this comparison is moot

## Community Sentiment

Sources: [r/archlinux](https://www.reddit.com/r/archlinux/comments/1j3i3us/nvidia_or_nvidiaopen_driver/), [r/linux_gaming](https://www.reddit.com/r/linux_gaming/comments/1gvngd1/state_of_gsp_firmware_with_nvidia_565_on_kde/), [Level1Techs](https://forum.level1techs.com/t/arch-having-issues-with-nvidia-or-nvidia-dkms-or-nvidia-open/232680), [GitHub #457](https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/457)

- NVIDIA engineer on GitHub #457: *"The GSP Issue on KDE is fixed and not present anymore since 575. Open modules are the suggested way to use NVIDIA on Linux :)"*
- But multiple Reddit users still report KDE Wayland stutter with GSP enabled, even on 580/590/595 drivers
- r/archlinux: *"I am using nvidia-dkms so that I can disable the GSP which is still causing stutter issues on KDE Wayland"*
- Level1Techs: *"Blackwell is not supported on any driver other than nvidia-open"*
- For Turing/Ampere/Lovelace users who CAN choose: the tradeoff is future-proofing (nvidia-open) vs stability with GSP off (nvidia-dkms)

## What You Give Up With nvidia-open

Since GSP firmware is technically optional but initramfs-rebuild-dependent on nvidia-open:

- **Can still mitigate KDE Wayland stutter** by disabling GSP — same `NVreg_EnableGpuFirmware=0` works, just needs `mkinitcpio -P` after changing modprobe config
- **Can still fix DisplayPort wake failures** — use `RMUseSwLinkTraining=1` as alternative (doesn't need initramfs rebuild since RegistryDwords are parsed by the nvidia module on every load, including from initramfs)
- **No escape hatch** for GSP firmware bugs on Blackwell — if you're affected, you must either disable GSP+rebuild initramfs or use software link training
- On Blackwell, this is moot — there's no alternative module

## Known Issues Specific to nvidia-open on Blackwell

| Issue | Affects | Source |
|-------|---------|--------|
| RTX 5060 Ti GSP crash — black screen, 100% fans, hard reset | 595.71.05, nvidia-open | [CachyOS Forum](https://discuss.cachyos.org/t/rtx-5060-ti-blackwell-gsp-firmware-crash-causes-gpu-lockup-black-screen-100-fans-hard-reset-required-on-nvidia-open-595-71-05/28856) |
| RTX 5070/RXT 5080 eGPU GSP timeout | 590/595 series | [NVIDIA Dev Forum](https://forums.developer.nvidia.com/t/590-release-feedback-discussion/353310?page=3) |
| GSP crash on RTX 3070 Mobile (HDMI) — Xid 120/154 | 580 series | [NVIDIA Dev Forum](https://forums.developer.nvidia.com/t/driver-580-gsp-firmware-crash-xid-120-154-on-rtx-3070-mobile-with-hdmi-display-535-works-with-gsp-disabled/364770) |
| Blackwell KVM passthrough GSP timeout | Unrecoverable | [NVIDIA Dev Forum](https://forums.developer.nvidia.com/t/nvidia-smi-no-devices-were-found-cannot-initialize-gsp-firmware-rm/370603) |

## Three-Sentence Summary

Blackwell GPUs require nvidia-open — the proprietary module doesn't support them. GSP firmware CAN be disabled on nvidia-open via the same `NVreg_EnableGpuFirmware=0` parameter, but requires an initramfs rebuild (`mkinitcpio -P`) because nvidia-open modules load early from the initramfs. For pre-Blackwell GPUs with nvidia-dkms, GSP can also be disabled and takes effect immediately on module reload without initramfs changes.

## Sources

- NVIDIA Developer Blog — Transition to open modules: https://developer.nvidia.com/blog/nvidia-transitions-fully-towards-open-source-gpu-kernel-modules/
- Phoronix — Arch Linux switches to nvidia-open: https://www.phoronix.com/news/Arch-LInux-NVIDIA-Open-Default
- NVIDIA Developer Forum — 5070 vs GSP firmware: https://forums.developer.nvidia.com/t/5070-vs-gsp-firmware/360585
- GitHub Discussion #457 — GSP issues fixed since 575: https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/457
- GitHub Discussion #680 — nvidia-dkms vs nvidia-open-dkms: https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/680
- Arch BBS — Can't disable GSP on nvidia-open: https://bbs.archlinux.org/viewtopic.php?id=300747
- Arch Wiki — NVIDIA GSP firmware issues: https://wiki.archlinux.org/title/NVIDIA
- Level1Techs — Blackwell not supported on proprietary: https://forum.level1techs.com/t/arch-having-issues-with-nvidia-or-nvidia-dkms-or-nvidia-open/232680
- r/archlinux — nvidia vs nvidia-open thread: https://www.reddit.com/r/archlinux/comments/1j3i3us/nvidia_or_nvidiaopen_driver/
- r/archlinux — Difference between nvidia-dkms and nvidia-open-dkms: https://www.reddit.com/r/archlinux/comments/1pt9bwi/is_there_a_difference_between_nvidiadkms_and/
- CachyOS Forum — RTX 5060 Ti GSP crash: https://discuss.cachyos.org/t/rtx-5060-ti-blackwell-gsp-firmware-crash-causes-gpu-lockup-black-screen-100-fans-hard-reset-required-on-nvidia-open-595-71-05/28856
- TechPowerUp — RTX 5060 Ti vBIOS update: https://www.techpowerup.com/337331/nvidia-issues-vbios-update-to-fix-rtx-5060-ti-reboot-black-screens
- NVIDIA Dev Forum — 580 GSP crash on RTX 3070 Mobile: https://forums.developer.nvidia.com/t/driver-580-gsp-firmware-crash-xid-120-154-on-rtx-3070-mobile-with-hdmi-display-535-works-with-gsp-disabled/364770
