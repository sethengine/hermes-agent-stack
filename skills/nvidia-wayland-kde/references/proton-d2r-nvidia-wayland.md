# Diablo 2 Resurrected — NVIDIA Wayland Proton Troubleshooting

## Platform
- Distro: Manjaro Linux
- GPU: RTX 5060 Ti
- Driver: NVIDIA 595 branch
- Display: KDE Plasma 6, Wayland
- Steam: D2R Infernal Edition (AppID 2536520)
- Proton: GE-Proton11-1

## Symptoms
1. Graphics settings (fullscreen, resolution, detail presets) don't persist across sessions
2. In-game frame limiter doesn't work — GPU receives uncapped frames
3. Game may launch in a fixed window with no resolution options
4. Occasional 1/4-screen render bug (top-left quadrant only)

## Fixed / Working Launch Options

### Best overall (MangoHud + XWayland fallback)
```
PROTON_ENABLE_WAYLAND=0 mangohud %command%
```

### With server selection (Battle.net region)
```
PROTON_ENABLE_WAYLAND=0 mangohud %command% -address us.actual.battle.net
```
Available regions: `-address us.actual.battle.net`, `eu.actual.battle.net`, `kr.actual.battle.net`

### Via gamescope (compositor-level cap)
```
gamescope -f -r 60 -- mangohud %command%
```

## MangoHud Config

```
~/.config/MangoHud/MangoHud.conf
```

```
fps_limit=60
no_display=1
```

`no_display=1` hides the HUD overlay — only the frame cap is active.

### ⚠️ MangoHud Pitfall: `vulkan_present_mode=immediate` + `fps_limit=0`

Two config mistakes that silently make MangoHud unable to cap FPS:

1. **`vulkan_present_mode=immediate`** — tells the Vulkan driver to present frames as fast as possible, bypassing MangoHud's frame pacing. Fix: use `mailbox` instead or remove the line entirely.
2. **`fps_limit=0`** — means unlimited. Must be a non-zero value to cap.

Check for both when a user reports "mangohud has no limit for fps".

## Proton Version Tracking

| Proton Version | Fullscreen | Settings Persist | Frame Limiter | Notes |
|---------------|------------|-----------------|---------------|-------|
| Stock Proton 10.0-3 | **Broken** | **Broken** | Broken | Most reports of issues on NVIDIA |
| GE-Proton10-29 | Fixed | Fixed | Broken (use mangohud) | Works but older GE |
| GE-Proton10-34 | Fixed | Fixed | Broken (use mangohud) | Most-recommended GE version |
| GE-Proton11-1 | ? (untested on 5060 Ti) | ? | Broken (use mangohud) | Should be equivalent to 10-34 |
| Proton Experimental | Fixed | Fixed | Broken (use mangohud) | Good alternative to GE |

## ProtonDB Findings (39 reports, Platinum rating)

### Users reporting success on NVIDIA 590/595 drivers:
- RTX 5070 Ti, Fedora 43, Proton 10.0-3, NVIDIA 590.44.01 — "Works perfectly OOTB"
- RTX 5070 Ti, Fedora 43, Proton 10.0-3, NVIDIA 580.119.02 — "Just install and play"
- RTX 5070 Ti, Bazzite, Proton 10.0-3, NVIDIA 590.44.01 — "No tinkering required"
- RTX 5080, CachyOS, CachyOS SLR Proton, NVIDIA 590.48.01 — "DLSS, Fullscreen, all graphics work"

### Users reporting issues (same driver family):
- RTX 3080, CachyOS, Proton 11.0 beta, NVIDIA 595.58.03 — ClientSDK folder needed, game works after
- RTX 3080, CachyOS, GE-Proton10-34, NVIDIA 595.58.03 — "Game will occasionally launch to windowed mode despite being set to full screen"
- RTX 3070, CachyOS, Proton 10.0-3, NVIDIA 590.48.01 — Fullscreen/DLSS all work, cursor flicker on controller
- RTX 3070, CachyOS, CachyOS SLR, NVIDIA 595.45.04 — "Works but ~3 crashes in 30h"
- RTX 3070 Ti, CachyOS, multiple drivers — "Crashes every 5-60 minutes across multiple distros"
- RTX 4070, CachyOS, GE-Proton10-34, NVIDIA 595.58.03 — Fullscreen fixed by switching from stock to GE
- RTX 4070 Ti, EndeavourOS, NVIDIA 580.82.07 — "Proton Experimental works, Proton 10 doesn't do fullscreen"
- RTX 3060 Ti, Pop!_OS, Proton Experimental, NVIDIA 535.86.05 — "Crashes in fullscreen, windowed mode solves it"

## Key Pattern

The 595 driver branch (used by RTX 5060 Ti) is the same family as the 590 series. Users who got GE-Proton or Proton Experimental running on 590/595 had working fullscreen and settings. The issues are not GPU-model-specific — they're Proton-version-specific.

## Frame Limiter Root Cause

**The in-game frame limiter cannot be made to work on NVIDIA Wayland.** It is not a config issue — it is an architectural incompatibility.

D2R's frame limiter (field `Framerate Cap` in `Settings.json`) uses a CPU sleep-based approach:
1. Game calculates target frame interval (e.g. 16.67ms for 60fps)
2. Game calls `Sleep()` for the required duration
3. Game calls `IDXGISwapChain::Present()` to show the frame

Under VKD3D-Proton + Wayland + NVIDIA, this fails at three independent layers:

1. **Wine Sleep is imprecise** — Wine's `Sleep()` has ~1-2ms granularity, not Windows' ~0.5ms. The game undersleeps.
2. **VKD3D swapchain decouples timing** — The game thread sleeps but VKD3D-Proton's internal Vulkan swapchain keeps presenting. The GPU renders at full speed through the queue. The game *thinks* it's capped but the swapchain is not.
3. **Wayland presentation model** — Wayland's `wl_surface::commit` + Vulkan `VK_PRESENT_MODE_IMMEDIATE_KHR` doesn't give the game the same vsync/cap control as X11's `PresentPixmap`.

From VKD3D-Proton maintainer (issue #1377): *"If you have a CPU fps limiter that's below vsync rate, the problem with that approach is horrible frame pacing usually"* and *"Disabling vsync makes all of this somewhat moot — we use fallback paths to pump latency fences when vsync is disabled."*

**There is no Proton env var or config that fixes this.** MangoHud (Vulkan-layer `fps_limit`) or Gamescope (`-r N`) are the only working solutions.

## Settings.json Reference

File location (D2R Infernal Edition Steam AppID 2536520):

```
~/.local/share/Steam/steamapps/compatdata/2536520/pfx/drive_c/users/steamuser/Saved Games/Diablo II Resurrected/Settings.json
```

Key fields affecting graphics and frame pacing:

```json
{
    "VSync": 0,                // 0=off, 1=on
    "Framerate Cap": 164,      // FPS limit (0=unlimited). DOES NOT WORK on NVIDIA Wayland.
    "Framerate Target": 0,     // 0=not set
    "NVIDIA DLSS": 2,          // 0=off, 1=Quality, 2=Balanced, 3=Performance, 4=Ultra Perf
    "Resolution Scale": 100,   // Render resolution percentage
    "Sharpening": 6,           // Sharpening strength
    "Window Mode": 1,          // 0=windowed, 1=fullscreen, 2=windowed fullscreen
    "Texture Anisotropy": 4,   // 0=off, 1=2x, 2=4x, 3=8x, 4=16x
    "Anti Aliasing": 0,        // 0=off, 1=SMAA, 2=FXAA
    "Dynamic Resolution Scaling": 0
}
```

## DLSS Upgrade Applied (Jul 8 2026)

### What was done

1. **DLSS DLL direct replacement** — `nvngx_dlss.dll` upgraded from D2R-shipped 14MB version to **310.7.0.0** (57MB, CL 37997616 = latest DLSS 4.x/5.x build). Also installed matching `nvngx_dlssg.dll` (frame gen, 7.2MB) and `nvngx_dlssd.dll` (depth, 40MB) from the same build. Old DLL backed up to `/tmp/d2r_dlss_backup/nvngx_dlss.dll`.

2. **OptiScaler v0.9.3 was briefly installed** but removed per user request. The user chose direct DLL replacement over proxy middleware. See SKILL.md "User Interaction Style" section — this is the user's preferred approach.

3. **Launch options updated to simplified form:**
```
/home/sethengine/.local/bin/d2r-dlss-update && mangohud %command%
```
The update script runs before every launch, checking for newer DLSS versions. No OptiScaler env vars needed.

4. **MangoHud** handles frame limiting via `fps_limit=164` in `~/.config/MangoHud/MangoHud.conf`.

### DLSS Indicator Not Visible

`PROTON_DLSS_INDICATOR=1` does not produce a visible on-screen overlay with the DLSS 310.7.0.0 release DLL. Despite GE-Proton correctly setting `DXVK_NVAPI_SET_NGX_DEBUG_OPTIONS=DLSSIndicator=1024,DLSSGIndicator=2,` and DXVK-NVAPI writing `ShowDlssIndicator=1024` to `HKLM\SOFTWARE\NVIDIA Corporation\Global\NGXCore`, the standard-release DLL's debug output goes to a log channel, not a screen HUD. The visual green DLSS indicator requires NVIDIA Profile Inspector or a debug build of the DLL.

To confirm DLAA is active: compare GPU usage at the same FPS cap between DLSS Quality and ultra_quality preset. DLAA (native res) will show higher GPU utilization at the same framerate.

## DLSS Auto-Update Script

`/home/sethengine/.local/bin/d2r-dlss-update` (also in skill as `scripts/d2r-dlss-update.py`):

- Fetches manifest from `https://loathingkernel.github.io/proton-upscalers/manifest.json`
- Finds latest non-dev DLSS SR/FG/Depth (sorted by `version_number` descending)
- Compares sizes with installed DLLs — replaces if different
- Backs up old DLLs to `/tmp/d2r-dlss-backups/`
- Installed as cron job: every Monday at 10:00 (job ID: 5e8e00d383ce)

## DLAA Forcing (No Native Toggle)

D2R has no DLAA option in the graphics menu. Force it via DXVK-NVAPI DRS:

Steam launch option:
```
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=ultra_quality" mangohud %command%
```

Steps:
1. Set DLSS to **Quality** in-game (keeps DLSS pipeline alive)
2. The DRS override forces the 310.7.0.0 DLL to render at native resolution + temporal AA only
3. MangoHud caps FPS as usual

The `ultra_quality` preset tells DLSS to skip upscaling and apply only the temporal anti-aliasing pass. Without `ngx_dlss_sr_override=on`, the render preset override is ignored.
