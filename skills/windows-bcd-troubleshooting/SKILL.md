---
name: windows-bcd-troubleshooting
description: Windows stuttery after bcdedit tweaks? Read BCD from Linux.
---

# Windows BCD troubleshooting from Linux

## When to use
- Windows side of a dual-boot is slow, stuttering, or "in slow motion" after the user ran bcdedit timer tweaks (`useplatformclock`, `tscsyncpolicy`, `disabledynamictick`, `useplatformtick`)
- User asks to check "bcdedit values" / the BCD — the Linux side is fine, the issue is Windows-only
- Need to inspect Windows boot configuration without booting Windows

## Core facts
- The Windows BCD is a registry hive (`\EFI\Microsoft\Boot\BCD`) in the Windows ESP. The ESP holding the LIVE BCD is the one Windows Boot Manager actually loads — find it from Linux boot entries (`efibootmgr -v` → `HD(n,...)\EFI\Microsoft\Boot\bootmgfw.efi`). It is often NOT the first ESP (this machine: Windows OS on nvme0n1p3, live BCD on nvme0n1p7; nvme0n1p1 is an empty leftover ESP).
- Backup copies usually sit beside it: `BCD.backup`, `bcd.bak` (plus `BCD.LOG*` journal files) — great for before/after diffs.

## Read-only workflow (no sudo needed — desktop polkit)
1. Mount the ESP read-only via udisks (no password on a desktop session):
   ```
   udisksctl mount -b /dev/nvme0n1p7          # → /run/media/$USER/<VOLID>
   udisksctl info -b /dev/nvme0n1p7           # confirm mount + ro
   ```
2. Read with libhivex (`hivexget` / `hivexsh`; package `hivex` / `libhivex-bin`).
   - **Pitfall: hivex paths use BACKSLASH separators** — `Objects\{GUID}\Elements\250000a6` — forward slashes fail with "subkey not found".
   - The per-element value lives in the subkey's `Element` value:
     ```
     hivexget <hive> 'Objects\{<guid>}\Elements\260000a2' 'Element'
     ```
   - Enumerate: pipe commands to `hivexsh`: `cd Objects\...` then `ls`, then `quit`.
3. Find the default OS entry: Boot Manager object `{9dea862c-5cdd-4e70-acc1-f32b344d4795}` element `0x23000003` (DefaultObject, GUID format) → the OS entry GUID.
4. Identify object roles via description element `0x12000004` ("Windows 11", "Windows Resume Application", "Windows Boot Manager", …). Don't confuse the resume object (winresume.efi) with a second OS — an OS entry's `0x23000003` "resumeobject" pointing at it is normal.
5. Read the timer elements (map in `references/bcd-element-ids.md`).
6. Unmount when done: `udisksctl unmount -b /dev/nvme0n1p7`

## Safety rules
- **NEVER write the BCD from Linux.** Editing a live hive externally (hivexregedit --merge, etc.) risks an unbootable Windows — BCD is journaled (BCD.LOG) and Windows owns its consistency. Hand the user exact `bcdedit` commands to run in Windows admin cmd instead. The user explicitly cares ("please do not break it").
- Keep the mount read-only; hivex reads only.
- Don't re-audit the Linux host when the symptom is Windows-specific (e.g., Linux TSC healthy + Windows slow ⇒ problem is in Windows config, go read the BCD).

## Known failure mode: Windows "slow motion" after timer tweaks
- Root cause found: **`useplatformclock` still = Yes (HPET forced)**. Forcing HPET on modern CPUs (Windows 10/11) causes system-wide slowdown, stutter, high DPC latency — reads as "everything in slow motion".
- Why a revert fails silently: **`bcdedit /set useplatformclock default` is INVALID** — boolean settings only accept `true`/`false`. The command errors, the old value stays. Verify in the hive: if element `0x260000A2` is still `01`, the revert did not happen.
- Fix — Windows admin cmd (TweakHub issue #2):
  ```
  bcdedit /deletevalue useplatformclock
  bcdedit /deletevalue disabledynamictick
  bcdedit /deletevalue tscsyncpolicy
  bcdedit /deletevalue useplatformtick
  ```
  "Element not found" = already default (fine). Verify: `bcdedit /enum {current}` → no useplatformclock/disabledynamictick/useplatformtick lines. Then reboot.
- A bad per-boot TSC calibration can also transiently slow Windows; a plain reboot sometimes clears it, but the durable fix is removing the HPET forcing. Full story + sources: `references/timer-tweak-failure-modes.md`.

## This user's system (sethengine)
- Manjaro + Windows 11 (en-GB) dual boot, second NVMe. Windows OS on nvme0n1p3; live BCD on nvme0n1p7 ESP.
- Windows 11 OS entry (as of 2026-08): `{fe36d625-3745-11f1-8bb8-eceb2b0ee349}`; resume entry `{fe36d624-3745-11f1-8bb8-eceb2b0ee349}`; Boot Manager `{9dea862c-5cdd-4e70-acc1-f32b344d4795}`. GUIDs can change if the entry is recreated.
- Linux TSC is healthy (constant_tsc, nonstop_tsc, ART at 5.1 GHz) — a Windows timer issue is Windows-side.
