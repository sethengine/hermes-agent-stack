---
source_session: 20260804_190930_aeb477
category: system
date: 2026-08-04
tags: [windows, bcd, bcdedit, hpet, useplatformclock, dual-boot, performance, tsc]
---

# Windows BCD Timer Tweak Landmine: `useplatformclock default` Revert Fails

## Symptom
Windows 11 (dual-boot on nvme0n1) runs in "slow motion" after reverting a BCD tweak script. Linux on the same CPU is perfectly fast — silicon TSC is healthy (`constant_tsc`, `nonstop_tsc`, `tsc_adjust`, ART, 5.1 GHz).

## Root cause: `bcdedit /set useplatformclock default` is invalid
`bcdedit` booleans only accept `true`/`false` — `default` errors out silently, so the old `Yes` stays. The booted entry still forces `useplatformclock` (HPET) plus leftover tweak values:

| Element | BCD ID | Forcing HPET? |
|---|---|---|
| `useplatformclock` | 0x260000A2 | ❌ the problem |
| `disabledynamictick` | 0x260000A5 | ❌ leftover |
| `tscsyncpolicy` | 0x250000A6 | ✅ reverted |
| `bootmenupolicy` | 0x250000C2 | ✅ normal |

Forcing HPET as platform clock causes massive DPC latency / system-wide slowdown on modern CPUs (Blur Busters, TweakHub).

## Correct fix (Windows admin cmd, then restart)
```cmd
bcdedit /deletevalue useplatformclock
bcdedit /deletevalue disabledynamictick
bcdedit /deletevalue tscsyncpolicy
bcdedit /deletevalue useplatformtick
```
"Element not found" = already default, fine. Verify: `bcdedit /enum {current}` shows NO `useplatformclock`/`disabledynamictick`/`useplatformtick` lines. Then `shutdown /r /t 0`.

## Reading the BCD from Linux (read-only)
- Windows BCD lives on the ESP that Windows Boot Manager actually loads — find it via `efibootmgr` / boot entry `HD(7,...)` (on this rig: nvme0n1p7, NOT p1 — p1 was an empty leftover ESP).
- Mount read-only via `udisksctl mount -o ro` (no sudo), export with `hivexregedit`/`hivexsh`. Backslash separators in hive paths.
- Check BCD backups (dec 2025 / jan 2025) to diff what a tweak script changed over time.

## Related
- [[kwin-compose-values-landmine]] — same pattern: stale "optimization" config survives and hurts
- [[kwin-systemd-environment-vars]]
