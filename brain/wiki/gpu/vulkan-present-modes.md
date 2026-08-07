# Vulkan Present Modes

**Source Session:** `20260706_194614_c828c3` (Diablo 2 Wayland Nvidia Settings)
**Date:** 2026-07-08
**Category:** gpu

## Modes

| Mode | Latency | Tearing | Use Case |
|------|---------|---------|----------|
| `immediate` | Lowest | Yes | Competitive games, every ms counts |
| `mailbox` | Low | No | Best all-rounder - triple-buffer, low latency |
| `fifo` | Highest | No | Traditional V-Sync, avoid for gaming |
| `fifo_relaxed` | Medium | Sometimes | V-Sync that breaks under load |

## MangoHud Configuration

```ini
vulkan_present_mode=mailbox
```

This overrides the game's requested present mode and takes precedence over `vsync=` if both are set. For D2R, `mailbox` is the sweet spot: low latency + no tearing, and the `fps_limit=60` cap handles frame pacing.

## Additional Modes

- `shared_demand_refresh`
- `shared_continuous_refresh`
- `fifo_latest_ready`

These are rarely used in gaming contexts.
