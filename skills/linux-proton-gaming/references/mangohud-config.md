# MangoHud Configuration Reference

Config file: `~/.config/MangoHud/MangoHud.conf`
Per-app override: `~/.config/MangoHud/<executable_name>.conf`
Env var override (takes priority): `MANGOHUD_CONFIG="key=val,key=val"`

## FPS LIMITING

| Option | Values | Notes |
|--------|--------|-------|
| `fps_limit=N` | `0`(unlimited) or integer | **`fps_limit=0` = unlimited** — common pitfall set by Goverlay |
| `fps_limit_method` | `early`(smoother) / `late`(lower latency) | `early` preferred for consistent frame pacing |
| `vulkan_present_mode` | `immediate*`,`mailbox`,`fifo`,`fifo_relaxed` | **`immediate` bypasses fps_limit entirely** — remove this if cap not working |
| `vsync` | `-1`(unset),`0`(adaptive),`1`(off),`2`(mailbox),`3`(on) | Values outside range silently ignored |
| `gl_vsync` | same as vsync | OpenGL only |
| `toggle_fps_limit` | keybind like `Shift_L+F1` | Cycles through comma-separated values in `fps_limit` |
| `show_fps_limit` | flag | Shows current FPS limit value on HUD |

## VISUAL OPTIONS

| Option | Values | Notes |
|--------|--------|-------|
| `no_display` | flag | Hides HUD completely. Toggle with `Shift_R+F12` |
| `fps_only` | flag | Shows ONLY the FPS number |
| `preset=N` | -1(default),0(hidden),1(fps only),2(horizontal),3(extended),4(all) | Overrides most other display params |
| `position` | `top-left`,`top-right`,`bottom-left`,`bottom-right`,`top-center`,`middle-left`,`middle-right` | |
| `hud_compact` | flag | Tighter row spacing |
| `horizontal` / `horizontal_stretch` | flag | Horizontal layout |
| `hud_no_margin` | flag | Removes padding |
| `font_size=N` | int | Main font (default 24) |
| `text_outline` / `text_outline_color` | flag / hex | White outline, black default |
| `background_alpha=0.5` | 0.0-1.0 | Background opacity |
| `alpha=1.0` | 0.0-1.0 | Whole HUD opacity |
| `round_corners=N` | int | Corner radius in px |
| `table_columns=N` | int | Column count (default 3) |
| `offset_x=N` / `offset_y=N` | int | Fine-tune position |
| `width=0` / `height=140` | int | Force dimensions |

## GPU STATS

| Option | What it shows |
|--------|-------------|
| `gpu_stats` | Enable GPU section |
| `gpu_temp` | GPU temp °C |
| `gpu_junction_temp` | Hotspot temp |
| `gpu_core_clock` | Core MHz |
| `gpu_mem_clock` | Memory MHz |
| `gpu_mem_temp` | VRAM temp |
| `gpu_power` / `gpu_power_limit` | Power draw/limit |
| `gpu_fan` | Fan speed (rpm AMD, % NVIDIA) |
| `gpu_voltage` | GPU voltage (AMD only) |
| `gpu_load_change` | Color-code GPU load by thresholds |
| `gpu_load_value=50,90` | Thresholds for color change |
| `gpu_load_color=C0C0C0,FFAA7F,CC0000` | Colors for below/above thresholds |
| `vram` / `vram_color` | VRAM used/total |

## CPU STATS

| Option | What it shows |
|--------|-------------|
| `cpu_stats` | Enable CPU section |
| `cpu_temp` | CPU package temp |
| `cpu_mhz` | CPU frequency |
| `cpu_power` | CPU power draw |
| `core_load` | Per-core load |
| `core_bars` | Per-core bars |
| `core_type` | Labels P-cores vs E-cores |
| `cpu_load_change` / `cpu_load_value` / `cpu_load_color` | Color-coding (same pattern as GPU) |

## MEMORY

| Option | What it shows |
|--------|-------------|
| `ram` | System RAM used/total |
| `swap` | Swap used/total |
| `procmem` | Per-process resident memory |
| `procmem_shared` / `procmem_virt` / `proc_vram` | Extended per-process |

## FRAMETIME GRAPH

| Option | Effect |
|--------|--------|
| `frame_timing` | Line graph |
| `frame_timing_detailed` | More detail |
| `dynamic_frame_timing` | Auto-scale |
| `histogram` | Histogram instead of line |
| `throttling_status` | Red indicator when throttling |

## FPS COLORS

| Option | Effect |
|--------|--------|
| `fps_color_change` | Enable threshold coloring |
| `fps_value=30,60` | Threshold values |
| `fps_color=B22222,FDFD09,39F900` | Red<30, yellow 30-60, green>60 |
| `fps_sampling_period=500` | Update interval (ms) |
| `fps_metrics=avg,0.01` | Show 1% and 0.1% lows |

## TOGGLE KEYBINDS

| Keybind | Action |
|---------|--------|
| `toggle_hud=Shift_R+F12` | Show/hide HUD |
| `toggle_hud_position=Shift_R+F11` | Cycle positions |
| `toggle_preset=Shift_R+F10` | Cycle presets |
| `toggle_fps_limit=Shift_L+F1` | Cycle fps_limit values |
| `toggle_logging=Shift_L+F2` | Start/stop logging |
| `reload_cfg=Shift_L+F4` | Reload config without restart |
| `reset_fps_metrics=Shift_R+F9` | Reset FPS min/max counters |

## OTHER

| Option | Effect |
|--------|--------|
| `blacklist=app1,app2` | Apps that never show HUD |
| `output_folder=/path` | For benchmark logging |
| `log_duration=N` / `log_interval=N` | Logging duration/interval |
| `permit_upload=1` | Enable upload to flightlessmango.com |
| `fcat` | FCAT overlay for frametime analysis |
| `media_player` / `media_player_name` | Spotify etc. metadata display |
| `network=eth0,wlo1` | Network throughput |
| `exec=custom command` | Display bash command output |
| `custom_text_center=` | Custom centered header text |
| `time` / `time_format="%T"` | System clock display |

## D2R-SPECIFIC SETUP

For Diablo 2 Resurrected, the minimum working config is a per-app file at `~/.config/MangoHud/diablo_ii_resurrected.conf`:

```ini
fps_limit=60
no_display=1
fps_limit_method=early
```

Steam launch option: `mangohud %command%`

**Common pitfalls:**
- `fps_limit=0` = unlimited (Goverlay sometimes writes this after editing)
- `vulkan_present_mode=immediate` breaks fps_limit entirely
- Old `vsync=4` from Goverlay is outside valid range and silently ignored
