---
source_session: 20260425_182841_54d6ea
extracted_date: 2026-07-22
category: software
tags: [manjaro, secure-boot, sbctl, uefi, boot]
---

# Manjaro Secure Boot Setup

Manjaro CAN boot with Secure Boot enabled, but it's not enabled by default and requires manual setup.

## Recommended Tools

- **sbctl** (recommended) — create/enroll own keys (PK/KEK/db), sign EFI binaries, set up automatic pacman signing hooks
- UKI (unified kernel images) — simpler chain of trust via EFI boot stubs
- GRUB requires extra signing support

## Key Steps

1. Check Secure Boot status: `sbctl status`
2. Create and enroll keys: `sbctl create-keys` then `sbctl enroll-keys -m`
3. Sign bootloader, kernel, and initramfs: `sbctl sign /boot/EFI/...`
4. Enable automatic signing via pacman hook (sbctl sets this up)
5. Reboot and verify

## Warnings

- Disable manufacturer keys for better security; back up UEFI vars first
- Some hardware (e.g., Lenovo laptops) may brick if OpROMs conflict — check devices first
- Protect UEFI with a strong password
- Use full disk encryption alongside Secure Boot
- Avoid third-party keys

## Compatibility

No official Manjaro Secure Boot wiki exists (pages 404). Arch Linux Wiki is the authoritative reference: `Unified Extensible Firmware Interface/Secure Boot`. Test on live USB first — disable Secure Boot for install, enable after.
