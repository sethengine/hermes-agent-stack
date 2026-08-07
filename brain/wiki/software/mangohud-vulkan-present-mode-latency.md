---
source_session: "20260707_181617_f5bd6e"
date: 2026-07-07
category: software
tags: [mangohud, vulkan, present_mode, latency, mailbox, immediate, frametime, gaming]
related: [linux-gaming-frame-limiters, vulkan-fps-cap-methods]
---

# MangoHud Vulkan Present Mode for Low Latency

MangoHud's `vulkan_present_mode` setting controls Vulkan swapchain presentation, which directly affects frame latency.

## Modes

| Mode | Sync | Latency | Tearing | Use case |
|------|------|---------|---------|----------|
| `immediate` | None | Lowest | Yes | Competitive FPS |
| `mailbox` | Triple-buffer | Low | No ✓ | General low-latency gaming |
| `fifo` | V-Sync | Highest | No | Visual quality priority |
| `fifo_relaxed` | Loose V-Sync | Med-High | Sometimes | Mixed |
| `shared_demand_re` | Dynamic | Adaptive | Sometimes | Adaptive sync displays |

## Recommended Config for D2R / Low-Latency Gaming

```ini
# ~/.config/MangoHud/MangoHud.conf
fps_limit=60
vulkan_present_mode=mailbox
```

`mailbox` is the sweet spot: triple-buffer gives tear-free output with significantly lower latency than `fifo` (double-buffer V-Sync). Combine with `fps_limit` to avoid GPU saturation.

## D2R-Specific: In-Game Limiter Broken

D2R's in-game frame limiter uses DirectX presentation timing (`IDXGISwapChain::Present`), which doesn't translate through DXVK/VKD3D to Vulkan under Proton/Wayland. Use MangoHud's `fps_limit` instead.

## References
- [[linux-gaming-frame-limiters]]
- [[vulkan-fps-cap-methods]]
