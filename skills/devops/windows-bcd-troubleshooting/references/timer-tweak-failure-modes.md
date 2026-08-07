# Windows timer BCD tweaks: failure modes & fixes

## The incident (2026-08, sethengine's rig)
Symptom: Windows 11 "running in slow motion" after the user tried to revert BCD timer settings (`tscsyncpolicy` to off, `useplatformclock` to default). Linux boot was perfect.

Actual BCD state in the booted OS entry `{fe36d625-3745-11f1-8bb8-eceb2b0ee349}`:
- `0x260000A2` useplatformclock = 1 (TRUE) ← still forcing HPET
- `0x250000A6` tscsyncpolicy = 0 (Default) ← revert succeeded
- `0x260000A5` disabledynamictick = 1 (TRUE) ← leftover tweak
- `0x250000C2` bootmenupolicy = 1 (Standard, normal); `0x25000020` nx = 0 (OptIn, normal)

Diagnosis: the "useplatformclock default" revert FAILED because bcdedit booleans only accept true/false — the invalid value was rejected and the old TRUE stayed. HPET-forced timing is the documented cause of system-wide slowdown on modern CPUs.

## Fix (Windows admin cmd)
```
bcdedit /deletevalue useplatformclock
bcdedit /deletevalue disabledynamictick
bcdedit /deletevalue tscsyncpolicy
bcdedit /deletevalue useplatformtick
```
- "Element not found" per command = already default, fine.
- Verify: `bcdedit /enum {current}` — no useplatformclock / disabledynamictick / useplatformtick lines.
- Reboot: `shutdown /r /t 0`.

## Why forcing HPET hurts
On Windows 10/11 the kernel prefers the invariant TSC (zero-latency, per-CPU). `useplatformclock true` forces the legacy HPET: every timer query goes to the motherboard chipset → massive DPC latency, CPU overhead, scheduler artifacts, stutter. It was a Windows 7-era tweak; on modern systems it is obsolete and actively harmful.

## Related knowledge
- Per-boot TSC calibration can transiently produce a wrong timebase → slow motion; a reboot may clear a bad calibration. But if `useplatformclock` is set, fix that first.
- `tscsyncpolicy` default (0) is fine on modern CPUs with invariant TSC; Enhanced (2) is a niche fix for multi-socket/core desync.
- Event viewer shows nothing for these; the BCD hive is the source of truth.

## Sources
- TweakHub issue #2 (exact fix + root cause): https://github.com/PrimeBuild-pc/TweakHub/issues/2
- Geoff Chappell BCD Elements (authoritative ID map): https://geoffchappell.com/notes/windows/boot/bcd/elements.htm
- Blur Busters: useplatformclock stutter threads: https://forums.blurbusters.com/viewtopic.php?t=13284 and https://forums.blurbusters.com/viewtopic.php?t=13775
- MS Community "Windows 11 slow motion or stuttering bug": https://techcommunity.microsoft.com/discussions/windows11/windows-11-slow-motion-or-stuttering-bug/4399949
