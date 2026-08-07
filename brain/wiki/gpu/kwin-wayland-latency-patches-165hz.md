---
source: "20260710_212706_69a41c"
date: "2026-07-10T19:06:43+00:00"
category: "gpu"
related: ["nvidia-wayland-kwin-latency-policy", "nvidia-595-grub-modprobe-env-kwin-config"]
---

# KWin Wayland Latency Patches for 165Hz Gaming

Jakub Okoński's June 2026 latency patches change KWin's compositor frame delivery scheduling.

## The Problem

KWin uses a fixed-presentation-timestamp model that guesses the next vblank and renders ahead. On NVIDIA Wayland the guess is often wrong because the EGL stream doesn't report vblank timing the same way Mesa does. Result: frames sit in the buffer 1-3ms longer than necessary. At 165Hz (6.06ms per frame), 3ms is half a frame of latency.

## The Fix

Instead of guessing, KWin queries the actual presentation clock from the DRM backend and schedules rendering to complete just before the real vblank. For Mesa/AMD this improves ~0.5ms; for NVIDIA it improves 1.5-3ms because the EGL stream timing mismatch is eliminated.

## Current Status

Patches target Plasma 6.8 (Wayland-exclusive release). Not available in Plasma 6.5.6.

## Workarounds for Current Versions

Set `GLPreferBufferSwap=0` (prefer mailbox/async swap) and `WindowsBlockCompositing=false` (prevent un-redirect stutter) in `~/.config/kwinrc` under `[Compositing]`.

References: [[nvidia-595-grub-modprobe-env-kwin-config]]
