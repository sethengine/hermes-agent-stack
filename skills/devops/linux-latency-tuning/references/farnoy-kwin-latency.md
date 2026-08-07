# KWin Compositor Latency Deep Dive (farnoy.dev, 2026-06)

## Source
[farnoy.dev/posts/linux-latency](https://farnoy.dev/posts/linux-latency) — LDAT-measured click-to-photon latency analysis on KDE Wayland 6.6.4, NVIDIA 595.58.03, Proton-GE 10-33, Ada RTX + Zen 4, LG C1 120Hz.

## Test Setup
- Teensy microcontroller acting as USB HID mouse + light sensor (Open Source LDAT sketch)
- NixOS on desktop + laptop (same config), Windows 11 on each for comparison
- KDE Wayland 6.6.4, Proton-GE 10-33, MangoHud 0.8.2 (late FPS limit)
- Desktop profile Zed editor added ~3ms latency to all windowed apps

## Key Findings

### 1. KWin Structural Latency Sources
| Source | Predicted | Actual | Delta | Root Cause |
|--------|-----------|--------|-------|------------|
| Render journal | 11.35ms (p50) | 2.06ms (p50) | 9.23ms | 2ms GPU render time floor + safety margin + timer slack |
| Safety margin | 1.46ms (p50) | - | - | Hardcoded 1ms minimum in DrmCommitThread |
| Timer slack | 1ms | 0.051ms (p99) | 0.949ms | QBasicTimer rounds to 1ms on Unix |

### 2. Render Journal Overestimation
KWin schedules compositing start based on `RenderJournal::result()` but actual GPU work is ~2ms. The 2ms floor in `glrendertimequery.cpp` line 78 prevents the journal from decaying below 2ms even when GPU compositing takes 0.36ms (p50 on 4090).

**Fix attempted:** Replace hard floor with p95 of 512-frame ring buffer. Faster decay toward measured value.

### 3. Timer Precision
Qt's `QBasicTimer` converts durations to milliseconds — everything rounds UP to the next ms. At 120Hz (8.3ms frame), 1ms = 12% waste. At 360Hz (2.78ms frame), 1ms = 36% waste.

**Fix:** timerfd + QSocketNotifier. Achieved 51us p99 wakeup deviation. Implemented in KWin's render loop thread only (DRM commit thread uses SCHED_RR + synchronous syscall, no slack).

### 4. Safety Margin (NVIDIA Path)
`KWIN_DRM_OVERRIDE_SAFETY_MARGIN` env var controls the minimum safety margin in DrmCommitThread. Default 1000 (1ms). Negative values allowed and "eat into" the margin contributed by other terms. At -150 on a 120Hz screen, effective margin ~0.3ms.

Code location: `src/backends/drm/drm_commit_thread.cpp` line 360-372
`m_baseSafetyMargin = vblankTime + s_safetyMarginMinimum`
`s_safetyMarginMinimum` = env var or 1000

### 5. Game-side Fixes (Measured)
| Fix | Impact | Notes |
|-----|--------|-------|
| PROTON_ENABLE_WAYLAND=1 | Largest win across all titles | Bypasses XWayland buffer queue |
| Late FPS limit (117 on 120Hz) | Clawed back V-Sync queue latency | Prevent frame buildup at refresh boundary |
| VKD3D_SWAPCHAIN_LATENCY_FRAMES=1 | Measurable on DX12 | Capped frame rate at half refresh with wine_wayland |
| DXVK_CONFIG latency frames | Minimal on DXVK 2.x+ | Already well-optimized |
| VRR | No significant impact | Neither helped nor hurt |

### 6. Cross-Platform Gap
With all fixes applied, Linux KDE Wayland min latency: ~3ms (input-to-present, windowed). Windows best measurements with VRR: ~4ms gap still existed. Patched KWin gained ~1.1-1.2ms in minimums.

### 7. Network Gaming (Sunshine + Moonlight)
- USB/IP over 2.5GbE: matches local performance (0.3ms RTT)
- Moonlight input-only: matches USB/IP latency
- Full Moonlight round-trip: kernel 7.0 regression (networking) on video stream start — workaround exists
- Windows Moonlight client slightly more responsive than Linux

## bpftrace Device
```bpftrace
tracepoint:syscalls:sys_enter_ioctl
/args->cmd == 0xc03864bc/
{
  $flags = *uptr((uint32 *)args->arg);
  @mode_atomic[$flags & 0x100 ? "test" : "commit"] = count();
}

interval:s:1 {
  print(@mode_atomic);
  clear(@mode_atomic);
}
```
When rate == refresh rate → zombie window keeping KWin busy.

## References
- Full article: https://farnoy.dev/posts/linux-latency
- MangoChill (input-driven FPS limiter): https://farnoy.dev/posts/mangochill
- wl_shm speed (Xaver Hugl): https://zamundaaa.github.io/wayland/2026/05/06/making-wl-shm-fast.html
