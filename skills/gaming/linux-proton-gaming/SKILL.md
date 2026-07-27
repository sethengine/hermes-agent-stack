---
name: linux-proton-gaming
version: "1.3.0"
description: "Troubleshoot Proton/DXVK/VKD3D gaming issues on Linux with NVIDIA+Wayland. Covers frame limiting, DLSS upgrades, graphics settings persistence, driver-level overrides, and debugging paths."
author: agent
---

# Linux Proton Gaming (NVIDIA + Wayland)

**Communication style for this class of work:** The user prefers extremely terse, command-focused responses. No explanations of why something works, no theory, no alternatives — just give the correct command or config change directly. When a fix fails, state what went wrong in one sentence and give the next command. Do not ask clarifying questions — list all options neutrally. Do not preface actions with "let me" or "I'll" — just do them. This preference governs ALL interactions within this skill's domain.

This skill covers recurring patterns when troubleshooting Steam Proton games on Linux with NVIDIA GPUs under Wayland. Tested on Manjaro + KDE Wayland + GE-Proton.

## Frame Limiter Issues

Many DX12 games have broken built-in frame limiters under Proton+VKD3D because they use CPU-side `Sleep()` timing that doesn't coordinate with the Vulkan swapchain.

**Working frame cap methods (priority order):**

1. **MangoHud** — hooks at Vulkan `vkQueuePresentKHR()` layer
   - Config: `~/.config/MangoHud/MangoHud.conf`
   - Key param: `fps_limit=60` (or comma list: `0,60,120` for toggle cycling)
   - **`fps_limit=0` = unlimited** — check this first if the cap isn't working; Goverlay sometimes writes 0
   - **`vulkan_present_mode=immediate` bypasses fps_limit entirely** — removes Vulkan frame pacing. Remove this line or set to `mailbox` (tear-free low-latency)
   - `vsync` valid range: -1 (unset) to 3. Values outside range are silently ignored.
   - `no_display=1` hides the overlay, keeps the cap
   - `fps_limit_method=early|late` — early is smoother, late is lower latency
   - Per-app overrides: `~/.config/MangoHud/<executable_name>.conf`
   - Launch: `mangohud %command%`
   - Env var override (takes priority over config file):
     `MANGOHUD_CONFIG="fps_limit=60,fps_limit_method=early,vulkan_present_mode=mailbox,no_display=1" mangohud %command%`
   - `no_display=1` hides the overlay, keeps the cap
   - `fps_limit_method=early|late` — early is smoother, late is lower latency
   - Per-app override: `~/.config/MangoHud/<executable_name>.conf`
   - Launch: `mangohud %command%`
   - Env var override (takes priority over config): `MANGOHUD_CONFIG="fps_limit=60,fps_limit_method=early,vulkan_present_mode=mailbox,no_display=1" mangohud %command%`

2. **Gamescope** — compositor-level hard cap
   - `gamescope -f -r 60 -- %command%`
   - Also fixes fullscreen/resolution issues since it handles mode setting

3. **NVIDIA nvidia-settings frame limiter** — DOES NOT work on Wayland (X11 only)

## DLSS DLL Upgrades

### The PROTON_DLSS_UPGRADE=1 problem

GE-Proton registers this env var via `check_environment()` but the download code in `protonfixes/upscalers.py` (`setup_upscalers()`) is never called from the main `proton` script. The env var is silently accepted and ignored.

### Manual replacement (the working approach)

1. Source manifest: [loathingkernel.github.io/proton-upscalers/manifest.json](https://loathingkernel.github.io/proton-upscalers/manifest.json)
2. Contains entries for: `dlss` (SR), `dlss_d` (depth), `dlss_g` (frame gen), `xess`, `fsr_31_dx12`, `fsr_31_vk`, `optiscaler`, `fsr_4*`
3. Filter out `is_dev_file` entries, sort by `version_number` descending, download `.xz` archives, decompress with `lzma`
4. Place DLLs in the game directory alongside the game exe — no special launch options needed (Windows DLL search loads from exe directory first)
5. Verify with `nvidia-smi` (clocks), or check Proton log for DLL loading paths

### Auto-update script pattern

```python
# Core flow:
manifest = fetch_json(MANIFEST_URL)
latest = [e for e in manifest['dlss'] if not e.get('is_dev_file')]
latest.sort(key=lambda x: x.get('version_number', 0), reverse=True)
# Download .xz, lzma.decompress, verify md5, write to game dir, backup old
```

Integration:
- **Steam launch option:** `/path/to/update-script && mangohud %command%` — runs before every launch
- **Cron:** weekly `no_agent=true` script job — keeps DLSS version current even without launching

### Auto-update script pattern

Write a Python script that:
1. Fetches the manifest
2. Filters non-dev entries, sorts by `version_number` descending
3. Downloads `.xz` archives, decompresses with `lzma`
4. Verifies MD5 checksum from manifest
5. Replaces DLLs in game directory
6. Backs up old DLLs before overwriting

Steam launch option integration:
```
/path/to/dlss-update-script && mangohud %command%
```

Cron integration: set up a weekly script-only cron job (no_agent=true) that runs the update script silently.

## Graphics Settings Not Saving

Common causes:
1. **Proton prefix file permissions** — `chown -R $USER:$USER ~/.local/share/Steam/steamapps/compatdata/<APPID>/`
2. **Read-only settings file** — check game's Settings.json/Documents in the prefix
3. **Nuke the prefix** — delete `compatdata/<APPID>/`, Steam recreates it on launch
4. **Launch option overrides** — some env vars override in-game configs

## Key DXVK/VKD3D Config

| Env var | Effect |
|---------|--------|
| `VKD3D_SWAPCHAIN_LATENCY_FRAMES=1` | Tightens GPU buffer count, may reduce input lag but can hurt performance |
| `DXVK_CONFIG="dxgi.syncInterval=0"` | DXGI present interval override (DXVK/DX11 only, not VKD3D/DX12) |
| `PROTON_ENABLE_NVAPI=1` | Enable DXVK-NVAPI (for DLSS/Reflex support) |
| `PROTON_ENABLE_WAYLAND=0` | Force XWayland instead of native Wayland — fixes some fullscreen/settings bugs |

## Game Input Issues on KDE Wayland (Cursor Capture Loss)

**Symptom:** Mouse cursor escapes the game window (turns into the KDE cursor, becomes non-interactive). The game's raw input capture breaks and falls through to the compositor.

### Root Cause

KWin's compositor can interfere with SDL's mouse confinement (`SDL_SetRelativeMouseMode` / `SDL_WarpMouseInWindow`). Under KDE Wayland, when the game loses focus momentarily (Alt+Tab, notification popup, Steam overlay), SDL may fail to recapture the cursor.

### Fixes (try in order)

1. **SDL mouse confine env var** — Steam launch options:
   ```
   SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0 %command%
   ```
   Prevents SDL from minimizing on focus loss, keeping mouse capture alive.

2. **Disable Steam Overlay** — Steam → game → Properties → uncheck "Enable Steam Overlay while in-game". The overlay can trigger a focus-loss→capture-release cycle.

3. **Force fullscreen exclusive mode** — add to launch options:
   ```
   SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS=0 %command% -fullscreen -window_mode exclusive
   ```

4. **Alt+Enter cycle** — when cursor is already lost mid-game, press Alt+Enter twice to force a window mode toggle that reinitializes mouse confinement.

5. **SDL_MOUSE_FOCUS_CLICKTHROUGH** — create/edit `~/.config/environment.d/gameenv.conf`:
   ```
   SDL_MOUSE_FOCUS_CLICKTHROUGH=1
   ```
   Then relog. Lets the game re-grab the mouse on click without requiring explicit focus.

6. **KWin compositor suspend for fullscreen** — System Settings → Display → Compositor → "Allow applications to block compositing" = ON. This prevents KWin from intercepting mouse events during exclusive fullscreen.

### Affected Games

- **Dota 2** (Source 2 engine, SDL2) — most commonly reported on KDE Wayland
- Any Source/Unity game using SDL raw mouse input under KDE Wayland

### References

- `references/dota-2.md` — Dota 2-specific settings and known issues
- SDL bug tracker: https://github.com/libsdl-org/SDL/issues (search "relative mouse mode Wayland")

## Steam Cloud Sync Errors (CEF Web Layer)

**Symptom:** Steam shows error code `-379` with "Failed to load web page (unknown error)" when trying to sync cloud saves. The error maps to Chromium's `ERR_HTTP_RESPONSE_CODE_FAILURE` — Steam's CEF browser received a non-2xx HTTP response from Valve's cloud sync API.

This is **not a general network issue** — Steam connects and games launch normally. It's a CEF subprocess failure against Valve's internal API endpoint.

### Root Cause

Steam's CEF (Chromium Embedded Framework) requests a cloud sync web page from `steamloopback.host` or Valve's API. When the server returns an error status (redirect loop, 502, 503, or similar), CEF raises `ERR_HTTP_RESPONSE_CODE_FAILURE` (-379).

On Linux, common triggers:
- **Bugged Proton prefix at compatdata/0/** — leftover from Proton installations can interfere with Steam's CEF initialization
- **Corrupted CEF cache** — `appcache/` and `package/` directories accumulate stale web state
- **Steam runtime update mismatch** — CEF binary updated but cache wasn't invalidated
- **Transient Valve backend issue** — server-side error that self-resolves
- **GPU→renderer IPC corruption over XWayland (NVIDIA Wayland)** — when GPU accelerated rendering is ON, NVIDIA's driver can corrupt IPC between the GPU process and renderer process, causing Chromium to terminate the renderer:
  ```
  ERROR:bad_message.cc(29)] Terminating renderer for bad IPC message, reason 213
  ```
  This manifests as the same Error -379 but in web views (Store, Library, cloud sync UI) rather than cloud sync specifically. The fix is gamescope (see "Steam Client Rendering Issues" section). `STEAM_FORCE_WAYLAND=1` is **not supported** by Steam's launch scripts and has no effect.
  Note: the cloud sync error differs from the store/library -379 — cloud sync error happens after login during sync attempt, store/library -379 happens when navigating web views. Check cef_log.txt for `bad_message` to confirm IPC corruption path.

### Fixes (try in order)

1. **Delete bugged Proton prefix (app ID 0)** — most common fix:
   ```bash
   rm -rf ~/.steam/steam/steamapps/compatdata/0/
   rm -rf ~/.local/share/Steam/steamapps/compatdata/0/
   ```
   Restart Steam afterward.

2. **Clear CEF web cache** — nuke all cached web state:
   ```bash
   killall steam
   sleep 2
   rm -rf ~/.steam/steam/appcache/*
   rm -rf ~/.steam/steam/package
   rm -rf ~/.steam/steam/depotcache/*
   ```

3. **Toggle Steam Beta / Stable** — Steam → Settings → Interface → Client Beta Participation. Switching forces a full CEF update/reinstall.

4. **Launch with sandbox disabled** (bypasses CEF sandbox issues):
   ```bash
   steam -no-cef-sandbox
   ```

5. **Check Valve backend** — transient outage:
   - https://steamstat.us
   - Try offline mode → then switch online

6. **Full CEF cache nuke** (nuclear option):
   ```bash
   killall steam
   sleep 2
   rm -rf ~/.steam/steam/appcache \
          ~/.steam/steam/depotcache \
          ~/.steam/steam/package \
          ~/.steam/steam/steamapps/shadercache \
          ~/.steam/steam/steamapps/temp \
          ~/.steam/steam/ubuntu12_32/steam-runtime
   ```

### Verification

Run this before and after fixes:
```bash
getent hosts steamloopback.host
```
Must return `127.0.0.1` instantly (no hang). Slow resolution means `/etc/nsswitch.conf` needs `mdns_minimal` instead of plain `mdns`:
```
hosts: mymachines mdns_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] files myhostname dns
```

### References

- `references/steam-cloud-sync-error-379.md` — error diagnostics and session evidence
- Chromium `net/base/net_error_list.h`: `NET_ERROR(HTTP_RESPONSE_CODE_FAILURE, -379)`
- https://wiki.archlinux.org/title/Steam/Troubleshooting#Very_long_startup_and_slow_user_interface_response

## Steam Client Rendering Issues (NVIDIA + Wayland)

The Steam client itself (not games) uses CEF/Chromium for web views (Store, Library, overlay). On NVIDIA + Wayland there's a known catch-22:

| Setting | Result |
|---------|--------|
| GPU accelerated rendering ON → Artifacts, flickering, corrupted rendering | CEF Chromium compositor interacts badly with XWayland + NVIDIA. Resizing the window clears it temporarily. |
| GPU accelerated rendering OFF → Extremely slow UI (~1fps at 3440×1440) | Software-only compositing (CPU renders everything). Disabled via NVIDIA blocklist in CEF. |

### Diagnosis

Check `~/.steam/steam/logs/webhelper_gpu.txt`:

```
gpu_compositing: disabled_software
disabled via blocklist, about:flags or the command line.
```

If all GPU memory buffers show `Software only`, GPU compositing is off.

When GPU accel IS enabled but Error -379 persists, check `~/.local/share/Steam/logs/cef_log.txt`:

```
ERROR:bad_message.cc(29)] Terminating renderer for bad IPC message, reason 213
ERROR:zygote_communication_linux.cc(292)] Failed to send GetTerminationStatus message to zygote
```

This means the GPU process IS running but the GPU→renderer IPC messages are corrupted over XWayland with NVIDIA's driver. Chromium kills the renderer on bad IPC, giving Error -379 and black squares where web views should render. This is distinct from the cloud-sync -379 documented below — same error code, different root cause chain.

### Fixes (try in order)

1. **Force GPU compositing past the blocklist** — launch Steam with Chromium flags:
   ```
   steam -ignore-gpu-blocklist -enable-gpu-rasterization
   ```
   Works on driver 595+ even though CEF blocklists NVIDIA on Wayland.

2. **Toggle GPU accel + resize window** — if artifacts appear:
   - Steam → Settings → Interface → Enable GPU accelerated rendering in web views → ON
   - Resize the Steam window — forces re-render, clears corruption
   - Most common daily-driver workaround (GitHub issues #10313, #10537)

3. **Re-enable KWin compositor for Steam** — if KWin compositing is OFF (common for latency tuning):
   ```
   #!/bin/sh
   kwinctrl set compositing on
   steam "$@"
   kwinctrl set compositing off
   ```
   Without a compositor, XWayland windows get no composition pass, making rendering bugs more visible.

4. **Run Steam inside gamescope (reliable fix)**:  
   `STEAM_FORCE_WAYLAND=1` is a **placebo** — it is NOT handled by Steam's launch scripts (`steam.sh`, `steamwebhelper.sh`). It does nothing. The proven fix is gamescope, which provides its own X11 environment, bypassing the host XWayland that corrupts CEF GPU IPC:

   ```
   gamescope -w 3440 -h 1440 -- steam
   ```

   When GPU accel is ON but Error -379 persists, check `cef_log.txt`:
   ```
   ERROR:bad_message.cc(29)] Terminating renderer for bad IPC message, reason 213
   ```
   The web helper IS running with GPU compositing enabled, but the GPU→renderer IPC messages are corrupted over XWayland. Chromium terminates the renderer, giving black web views and Error -379.

   This also manifests as "cannot connect to internet" in the Steam UI — the store/library web views fail to render, which looks like a network error. Actual network connectivity is fine (Steam downloads manifests, curl to Steam servers succeeds, SteamID gets set).

   **Desktop entry wrapper (persistent fix):**

   ```bash
   #!/bin/bash
   # ~/.local/bin/steam-wrapper
   qdbus org.kde.KWin /Compositor resume 2>/dev/null
   gamescope -w 3440 -h 1440 -- steam "$@"
   sleep 2
   qdbus org.kde.KWin /Compositor suspend 2>/dev/null
   ```

   Then set the desktop entry:
   ```
   Exec=/home/user/.local/bin/steam-wrapper %U
   ```

   The wrapper enables KWin compositor (fixes XWayland window composition), runs Steam inside gamescope (clean X11 environment, no IPC corruption), then suspends compositor after exit (back to game latency mode).

### Mitigations when GPU accel is off

Create `~/.steam/steam/steam_dev.cfg`:
```
@nClientDownloadEnableHTTP2PlatformLinux 0
unShaderBackgroundProcessingThreads 6
```

### Known issues

- [#10313](https://github.com/ValveSoftware/steam-for-linux/issues/10313) — Store flicker on NVIDIA Wayland (Dec 2023)
- [#10537](https://github.com/ValveSoftware/steam-for-linux/issues/10537) — Corrupted right-click menus with GPU accel ON
- [#13151](https://github.com/ValveSoftware/steam-for-linux/issues/13151) — GPU accel defaults to OFF on NVIDIA+Wayland (May 2026)
- Persists across driver versions 545→595 — requires Valve CEF fix, not NVIDIA

See `references/steam-client-wayland-issues.md` for diagnostic trace detail.

## DLAA via DXVK-NVAPI DRS

Force DLAA (native resolution, no upscaling, just temporal AA) via DRS settings in Steam launch options. **This requires DXVK-NVAPI built with R610+ headers** — GE-Proton11-1 ships v0.9.2 (R595) which does NOT recognize the DLAA-related setting IDs.

### Verification in Proton Log

Add `PROTON_LOG=1` to launch options, then check `~/steam-<APPID>.log`:

**R595 (not recognized):**
```
Applying the following DRS settings when requested by the application (1 total):
    0x10e41df2/Unknown = Setting not found
```

**R610+ (recognized):**
```
Applying the following DRS settings when requested by the application (2 total):
    0x10e41e01/Enable DLSS-SR override = 0x1
    0x10e41df4/Override DLSS mode to be DLAA = 0x1
```

### Building DXVK-NVAPI from Source

When GE-Proton ships a version without the needed DRS settings:

```bash
sudo pacman -S mingw-w64-toolchain          # Install MinGW
git clone --recurse-submodules https://github.com/jp7677/dxvk-nvapi.git
cd dxvk-nvapi
./package-release.sh master /tmp/dxvk-nvapi-build --enable-tests

# Replace bundled 64-bit DLL
# Backup first!
cp /path/to/GE-Proton-XX/files/lib/wine/nvapi/x86_64-windows/nvapi64.dll /tmp/nvapi64.bak
cp /tmp/dxvk-nvapi-build/dxvk-nvapi-master/x64/nvapi64.dll /path/to/GE-Proton-XX/files/lib/wine/nvapi/x86_64-windows/nvapi64.dll
```

Verify the new build loaded by checking Proton log for the version string (`DXVK-NVAPI v0.9.2-N-githash`).

### DRS Env Var — Comma Issue

Steam's launch option parser can eat commas inside `DXVK_NVAPI_DRS_SETTINGS`, causing the log to show `Applying (1 total)` instead of `(N total)`. Three workarounds, in priority order:

#### 1. Individual Env Vars (most reliable)

DXVK-NVAPI's `enrichwithenv()` also picks up individually named env vars matching `DXVK_NVAPI_DRS_<NGX_CONSTANT_NAME>=<value>`. These bypass the comma issue entirely — each setting is its own env var:

```
DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1 DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1 mangohud %command%
```

#### 2. Hex ID Approach (fallback)

Text keys are parsed through a name→ID lookup table in DXVK-NVAPI. Use hex IDs when text keys fail:

```
DXVK_NVAPI_DRS_SETTINGS="0x10E41E01=1,0x10E41DF4=1" mangohud %command%
```

Where:
- `0x10E41E01` = `NGX_DLSS_SR_OVERRIDE_ID` (value 1 = enable)
- `0x10E41DF4` = `NGX_DLAA_OVERRIDE_ID` (value 1 = `NGX_DLAA_OVERRIDE_DLAA_ON`)

#### 3. Text keys in DRS_SETTINGS (least reliable)

```
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=dlaa"
```

⚠️ Text key `ngx_dlss_sr_override_render_preset_selection` maps to setting ID `0x10E41DF2` which does NOT exist in R610 headers. The correct DLAA route is `NGX_DLAA_OVERRIDE` at ID `0x10E41DF4`, reachable only via hex ID or the `DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1` individual env var.

### DRS Setting ID Reference (R610 headers, NVAPI R595+)

From `external/nvapi/NvApiDriverSettings.h`:

| Setting ID | Constant | Type | Values |
|-----------|----------|------|--------|
| `0x10E41E01` | `NGX_DLSS_SR_OVERRIDE_ID` | Bool | 0/1 (off/on) |
| `0x10E41DF4` | `NGX_DLAA_OVERRIDE_ID` | Enum | 0 (`DLAA_DEFAULT`), 1 (`DLAA_ON`) |
| `0x10E41DF3` | `NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION_ID` | Enum | `RENDER_PRESET_A`–`Z`, `_Default`, `_Latest` |
| `0x10E41DF5` | `NGX_DLSS_SR_OVERRIDE_SCALING_RATIO_ID` | Float | Ratio value |
| `0x10E41DF1` | `NGX_DLSS_FG_OVERRIDE_RENDER_PRESET_SELECTION_ID` | Enum | render presets |
| `0x10E41DF2` | `NGX_DLSS_RR_OVERRIDE_RENDER_PRESET_SELECTION_ID` | Enum | render presets (Ray Reconstruction) |
| `0x10AFB76A` | performance mode override | Enum | perf ratios |

Note: `0x10E41DF2` is the RR (Ray Reconstruction) preset selection, NOT an SR/DLAA setting. The `ngx_dlss_rr_override_render_preset_selection` text key maps here.

### Building DXVK-NVAPI from Source

When GE-Proton ships a version without the needed DRS settings:

```bash
# Install MinGW (Manjaro)
sudo pacman -S mingw-w64-toolchain

# Clone and build
git clone --recurse-submodules https://github.com/jp7677/dxvk-nvapi.git
cd dxvk-nvapi
./package-release.sh master /tmp/dxvk-nvapi-build --enable-tests

# Replace bundled DLL
cp /tmp/dxvk-nvapi-build/dxvk-nvapi-master/x64/nvapi64.dll \\
  ~/.local/share/Steam/compatibilitytools.d/<GE-Proton>/files/lib/wine/nvapi/x86_64-windows/nvapi64.dll
```

Back up the original first.

### DRS Setting Reference (R610+)

| DRS Key | Purpose | Example Value |
|---------|---------|---------------|
| `ngx_dlss_sr_override` | Enable DLSS SR override | `on` |
| `ngx_dlss_sr_override_render_preset_selection` | Set SR render preset | `dlaa`, `ultra_quality`, `default` |
| `ngx_dlaa_override` | Direct DLAA override | `on` |
| `ngx_dlss_rr_override` | Enable Ray Reconstruction override | `on` |
| `ngx_dlss_rr_override_render_preset_selection` | Set RR render preset | `default` |
| `ngx_dlss_fg_override` | Enable Frame Generation override | `on` |
| `ngx_dlss_fg_override_render_preset_selection` | Set FG render preset | `default` |

### DRS Env Var — Comma Issue

Steam's launch option parser can eat commas inside `DXVK_NVAPI_DRS_SETTINGS`, causing the log to show `Applying (1 total)` instead of `(N total)`. Two workarounds:

#### Individual Env Vars (most reliable)

DXVK-NVAPI's `enrichwithenv()` also picks up individually named env vars matching `DXVK_NVAPI_DRS_NGX_<SETTING_NAME>=<value>`. These bypass the comma issue entirely:

```
DXVK_NVAPI_DRS_NGX_DLSS_SR_OVERRIDE=1 DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1
```

#### Hex ID Approach (fallback)

Text keys are parsed through a name->ID lookup table. Use hex IDs when text keys fail:

```
DXVK_NVAPI_DRS_SETTINGS="0x10E41E01=1,0x10E41DF4=1"
```

Where:
- `0x10E41E01` = `NGX_DLSS_SR_OVERRIDE_ID` (value 1 = enable)
- `0x10E41DF4` = `NGX_DLAA_OVERRIDE_ID` (value 1 = `NGX_DLAA_OVERRIDE_DLAA_ON`)

Note: the log shows `0x10E41DF2/Unknown = Setting not found` for text key `ngx_dlss_sr_override_render_preset_selection`. This maps to ID `0x10E41DF2` which does not exist in R610 headers. The correct DLAA setting is `NGX_DLAA_OVERRIDE` at ID `0x10E41DF4`, not a render preset selection.

### Full DLAA Launch Option (R610+)

```
DXVK_NVAPI_DRS_SETTINGS="ngx_dlss_sr_override=on,ngx_dlss_sr_override_render_preset_selection=dlaa" PROTON_ENABLE_NVAPI=1 mangohud %command%
```

Or using hex IDs (bypasses text lookup issues):
```
PROTON_ENABLE_NVAPI=1 DXVK_NVAPI_DRS_SETTINGS="0x10E41E01=1,0x10E41DF4=1" mangohud %command%
```

Set DLSS to Quality in-game (keeps the DLSS pipeline active), the DRS override forces native resolution rendering.

### DRS Setting ID Reference (R610 headers)

From `external/nvapi/NvApiDriverSettings.h`:

| Setting ID | Constant | DRS text key | Values |
|-----------|----------|-------------|--------|
| `0x10E41E01` | `NGX_DLSS_SR_OVERRIDE_ID` | `ngx_dlss_sr_override` | 0/1 (off/on) |
| `0x10E41DF3` | `NGX_DLSS_SR_OVERRIDE_RENDER_PRESET_SELECTION_ID` | `ngx_dlss_sr_override_render_preset_selection` | `render_preset_a`–`z`, `render_preset_latest`, `render_preset_default` |
| `0x10E41DF4` | `NGX_DLAA_OVERRIDE_ID` | `ngx_dlaa_override` | `dlaa_default`(0), `dlaa_on`(1) |
| `0x10E41DF5` | `NGX_DLSS_SR_OVERRIDE_SCALING_RATIO_ID` | `ngx_dlss_sr_override_scaling_ratio` | Float ratio value |
| `0x10E41DF1` | `NGX_DLSS_FG_OVERRIDE_RENDER_PRESET_SELECTION_ID` | `ngx_dlss_fg_override_render_preset_selection` | render presets |
| `0x10E41DF2` | `NGX_DLSS_RR_OVERRIDE_RENDER_PRESET_SELECTION_ID` | `ngx_dlss_rr_override_render_preset_selection` | render presets |
| `0x10AFB76A` | `NGX_DLSS_SR_OVERRIDE_SCALING_RATIO_ID` | (performance mode) | perf ratios |

### DLSS Debug Indicator

`PROTON_DLSS_INDICATOR=1` enables `DXVK_NVAPI_SET_NGX_DEBUG_OPTIONS` which writes `ShowDlssIndicator` and `DLSSG_IndicatorText` to the NGX registry. However, this produces **no visible overlay on Linux** — the registry keys control NGX debug logging, not a screen HUD. The visual green DLSS indicator requires NVIDIA Profile Inspector on Windows.

## nvidia-powerd

- Purpose: Implements **Dynamic Boost** — shifts power between GPU and CPU within a shared thermal/power budget
- Documented requirement: **Notebook form factor** (from NVIDIA's driver README: `/usr/share/doc/nvidia/html/dynamicboost.html`)
- Also supports some enterprise/datacenter GPUs (GB200 etc.)
- Desktop GPUs (ANY desktop, including RTX 5060 Ti) are NOT supported — exits immediately with:
  `ERROR! Running on an unsupported system (PCI device Id: 0x....)`
- The daemon starts and exits in ~28ms (`Duration: 28ms` in systemd status) — it does NOT stay running
- `Restart=on-abort` in the systemd service means it restarts only on crashes, not on a clean exit

## VKD3D-Proton Frame Pacing Notes

From Hans-Kristian (vkd3d-proton maintainer):
"If you have a CPU fps limiter that's below vsync rate, the problem with that approach is horrible frame pacing usually, but a VRR monitor can clean that up."

Game sleep-based frame limiters are fundamentally incompatible with VKD3D-Proton's Vulkan swapchain management. No Proton env var can fix it — use MangoHud or Gamescope instead.

### Diagnosing DRS Override Application

When a DRS setting isn't working, use PROTON_LOG=1 to capture the Proton log, then check:

```
grep -i "drs|setting|nvapi" ~/steam-<APPID>.log | grep -v OutputDebugString
```

Look for:
- DXVK-NVAPI version line — confirms which version is loaded
- Applying the following DRS settings (N total) — N should match your override count
- Setting not found — the DRS key ID is unknown to this DXVK-NVAPI version

## nvidia-powerd (Dynamic Boost)

`nvidia-powerd` implements NVIDIA Dynamic Boost — shifts power between GPU and CPU within a shared thermal/power budget.

- Documented requirement per NVIDIA driver README (`/usr/share/doc/nvidia/html/dynamicboost.html`): **Notebook form factor**
- Desktop GPUs (ANY desktop) are NOT supported — exits immediately with:
  `ERROR! Running on an unsupported system (PCI device Id: 0x....)`
- The daemon runs for ~28ms then exits — systemd shows `Duration: 28ms`
- Does NOT affect frame limiting on desktop
- Also supports some enterprise/datacenter GPUs (GB200 etc.), not consumer desktop

## VKD3D-Proton Frame Pacing

From Hans-Kristian (vkd3d-proton maintainer, issue #1377):
> "If you have a CPU fps limiter that's below vsync rate, the problem with that approach is horrible frame pacing usually, but a VRR monitor can clean that up."

Game sleep-based frame limiters are fundamentally incompatible with VKD3D-Proton's Vulkan swapchain management. No Proton env var can fix it — use MangoHud or Gamescope instead.

### Diagnosing DRS Override Application

When a DRS setting isn't working:

```bash
PROTON_LOG=1
# Launch game, then:
grep -i "drs\|setting\|nvapi" ~/steam-<APPID>.log | grep -v OutputDebugString
```

Look for:
- DXVK-NVAPI version line — confirms which version is loaded
- `Applying the following DRS settings when requested by the application (N total)` — N should match override count
- `Setting not found` — the DRS key ID is unknown to this DXVK-NVAPI version

## Useful References

- `references/d2r-infernal-edition.md` — D2R-specific settings, DLSS paths, and known issues
- `references/dota-2.md` — Dota 2 settings, mouse cursor capture, cloud sync fixes
- `references/mangohud-config.md` — Comprehensive MangoHud configuration option reference
- `references/steam-client-wayland-issues.md` — Steam client rendering issues on NVIDIA + Wayland (diagnosis, workarounds, upstream issues)
- `references/steam-cloud-sync-error-379.md` — Steam error -379 diagnostics and CEF web layer troubleshooting
- `scripts/dlss-update.py` — Generic DLSS DLL auto-updater using the loathingkernel manifest. Reusable for any game with DLSS support. Run as `python scripts/dlss-update.py /path/to/game` or set `DLSS_DIR`.
- References for other games can be added under `references/<game>.md`
