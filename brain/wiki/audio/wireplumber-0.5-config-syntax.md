---
source_session: 20260703_202938_ecafcd
date: 2026-07-25
category: audio
tags: [wireplumber, 0.5, spa-json, lua, config, pipewire]
---

# WirePlumber 0.5 Config Syntax (SPA-JSON vs Lua)

**WirePlumber 0.5** (current on Manjaro) uses **SPA-JSON `.conf` syntax** instead of the old Lua table-based API from WP 0.4.

## Key Changes

| Feature | WP 0.4 (old) | WP 0.5 (current) |
|---------|-------------|-------------------|
| Config files | `main.lua.d/*.lua` | `wireplumber.conf.d/*.conf` |
| Format | Lua tables | SPA-JSON (SPA props format) |
| Rules API | `table.insert(alsa_monitor.rules, ...)` | Does not exist |

## What Works in WP 0.5

The old approach — Lua files with `alsa_monitor.rules` — **silently fails** on WP 0.5. The `alsa_monitor` object and its `.rules` table don't exist in the new architecture.

For per-application quantum (e.g., Chrome):
```bash
# Simple per-app quantum via pw-metadata (works on WP 0.5)
pw-metadata -n settings 0 clock.force-quantum 256
```

For persistent config, create `.conf` files:
```bash
mkdir -p ~/.config/wireplumber/wireplumber.conf.d
```

## Recovery from Bad Config

If a bad WP 0.4 Lua config was written:
```bash
rm -rf ~/.config/wireplumber
systemctl --user restart wireplumber pipewire pipewire-pulse
```

[[pipewire-config-chaos-quantum-conflicts]]
[[pipewire-low-latency-config]]
