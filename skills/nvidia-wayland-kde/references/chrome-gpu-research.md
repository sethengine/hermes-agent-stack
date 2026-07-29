# Chrome GPU on NVIDIA + Wayland — Research Notes

## VAAPI Video Decode on NVIDIA — Chrome vs Firefox Quality

### Core Problem: Chrome Uses `vaPutSurface`, Firefox Uses WebRender

Chrome's VAAPI decoder uses `vaPutSurface()` to transfer decoded frames to the display. This API was designed for video wall/post-processing, not rendering. It applies **bilinear (or nearest-neighbor) chroma upsampling** — the cheapest filter for reconstructing color from 4:2:0 video. This causes:
- Soft/blurry chroma detail
- Visible banding in gradients (sky, shadows, skin tones)
- Color bleeding on edges

**Chromium bug:** [crbug.com/40210909](https://issues.chromium.org/issues/40210909) — "vaPutSurface reduces the video quality by applying low quality filters for rendering the picture."

Firefox avoids this by retrieving decoded surfaces via `vaGetImage()`/`vaDeriveImage()` and rendering through its own WebRender compositor with proper shaders for chroma upsampling.

### No 10-bit (HDR/Wide Color) Decode in Chromium VAAPI

**Chromium bug:** [crbug.com/349428388](https://issues.chromium.org/issues/349428388) — "10-bit Video Decoding Not Supported by Chromium's Linux VA-API Decoder."

Chromium's VAAPI decoder does NOT support HEVC Main10 or VP9 Profile2 (10-bit color depth). This means:
- Any HDR video content → falls back to software decode
- Software decode of 10-bit may apply incorrect tone mapping → banding, washed-out colors, crushed blacks
- Firefox handles 10-bit properly through VDPAU or Vulkan Video

The VAAPI driver (`libva-nvidia-driver`) itself supports HEVCMain10 and VP9Profile2 — the limitation is in Chrome's decoder, not the driver.

### `disable_rgb_to_yuv_conversion` Workaround

Chrome has an active driver bug workaround on NVIDIA Linux:
```
Disable RGB to YUV hardware conversion on NVIDIA Linux:
  (http://crbug.com/447709687)
  Applied Workarounds: disable_rgb_to_yuv_conversion
```

This workaround disables a hardware conversion path that is broken on NVIDIA, forcing Chrome to use a software fallback for RGB→YUV. This affects video encoding and some compositing paths.

### Firefox 153 Vulkan Video — The Real Fix (June 2026)

**Firefox 153** (ships July 2026) has merged initial support for Vulkan Video decoding ([Phoronix](https://www.phoronix.com/news/Firefox-Vulkan-Video-Merged), [merged June 8, 2026](https://news.slashdot.org/story/26/06/08/1630210/firefox-merges-support-for-vulkan-video-decoding)). This is the most significant development for NVIDIA Linux video quality because:

- NVIDIA themselves implemented the Vulkan Video decode path in Firefox
- Bypasses VAAPI entirely → **no vaPutSurface, no libva-nvidia-driver translation layer**
- Vulkan handles YUV surfaces natively with proper chroma upsampling
- Reddit r/linux: *"finally, Nvidia users won't need to jump through hoops just to watch youtube without their cpu melting"*
- HN: *"This is great news for nvidia users on Linux. It means that they don't need to install a VAAPI compatibility tool like nvidia-vaapi-driver."*

**This is the fix for the banding issue on NVIDIA Linux.** There is no equivalent fix coming to Chrome — NVIDIA has expressed interest in helping with Chrome Vulkan Video ([Phoronix](https://www.phoronix.com/news/NVIDIA-Vulkan-Video-Chrome-Help)) but nothing has shipped.

### Chrome's VAAPI Video Quality — Last 30 Days Status

There is **no fix in flight** for Chrome's video quality issues on NVIDIA Linux:

- **Chromium issue #40210909** (vaPutSurface low-quality chroma) — still open, unassigned
- **Chromium issue #349428388** (10-bit decode not supported) — still open
- **Chrome Vulkan Video decoder** — Feasibility design exists ([Khronos](https://www.khronos.org/vulkan/chrome-video/vulkan_video_integration.html)), NVIDIA interested, but zero code landed
- **Firefox 153 Vulkan Video** — shipped June 2026, now the recommended path

### How to test Firefox 153 Vulkan Video early

```bash
sudo pacman -S firefox-nightly
# Or grab Firefox 153 beta when available
```

In `about:config`, ensure:
```
gfx.webrender.all=true
media.hardware-video-decoding.enabled=true
```

The `gfx.webrender.all=true` enables WebRender (already default on most systems), and `media.hardware-video-decoding.enabled=true` enables Vulkan Video decode path.

### `--use-angle=vulkan` on Wayland — Chromium 129+ Upstream Fix

Since **Chromium 129** (CL 5568860, mid-2024), `--use-angle=vulkan` on Wayland was unblocked upstream ([Thorium issue #687](https://github.com/Alex313031/thorium/issues/687)). This works on **AMD/Intel** GPUs with Mesa RADV. On those GPUs, the Vulkan ANGLE backend provides the correct code path for VAAPI video decode.

On **NVIDIA + Wayland**: Despite `chrome://gpu` showing "Vulkan: Enabled" (API 1.4.350+) with populated Vulkan Information, `--use-angle=vulkan` still **crashes the GPU process** on NVIDIA + Wayland. The GPU falls back to software rendering entirely. `--use-gl=angle` without `--use-angle=vulkan` is the only working path.

### Xwayland Does Not Fix Banding

Running Chrome on Xwayland (`--ozone-platform=x11` on a Wayland session) does NOT fix the banding. The `vaPutSurface` chroma upsampling quality issue is in Chrome's **VAAPI decoder** (`media/gpu/vaapi/`), which runs before any display backend:

```
Video → VAAPI decoder → vaPutSurface (bilinear chroma ✗) → GL renderer → display backend
```

| Backend | GL Path | vaPutSurface Quality | Result |
|---------|---------|---------------------|--------|
| Native Wayland | ANGLE OpenGL ES | Degraded | Banding |
| Xwayland | Native GLX | Same degraded | Same banding |

The quality loss happens at the vaPutSurface step, unchanged by the GL or display backend. The only fix is bypassing VAAPI entirely (Firefox 153 Vulkan Video).

### Confirming Hardware Decode is Actually in Use

**chrome://media-internals (per-video confirmation):**

chrome://gpu only shows *capability*, not actual usage. For per-video confirmation:
1. Open `chrome://media-internals`
2. Play a video, then click the entry in the list
3. Search for these properties:
```
kVideoDecoderName: "VaapiVideoDecoder"   → hardware decode in use
kIsPlatformVideoDecoder: true             → confirm hardware
VideoDecoderPipeline |decoder_| Initialize() successful  → init OK
```
If you see `"FFmpegVideoDecoder"` instead, it's software decoding despite chrome://gpu saying "Hardware accelerated".

**nvtop (real-time GPU engine monitoring):**
```bash
nvtop
```
While a video plays, check the **DEC** engine column. If DEC shows utilization (e.g., 10-40%), hardware decode is active. If DEC stays at 0%, it's software decode.

**Chrome DevTools Media Tab:**
1. Open DevTools (F12) → **Media** tab
2. Play a video, click the player entry
3. Look for `Hardware decoder: true` under "Video Decoder"
4. If `false` or `FFmpegVideoDecoder` → software decode

### The `UseMultiPlaneFormatForHardwareVideo` + `disable_rgb_to_yuv_conversion` Interaction

`UseMultiPlaneFormatForHardwareVideo` tries to keep video frames in YUV multi-plane texture format through the GL pipeline, avoiding the RGB conversion that loses precision. However, on NVIDIA Linux, Chrome has an active workaround that disables hardware RGB→YUV conversion (crbug.com/447709687) because it's buggy on NVIDIA.

Net effect:
- Multi-plane YUV textures work for IMPORT from decoder
- But any conversion between YUV and RGB goes through software fallback
- This limits the quality benefit of UseMultiPlaneFormatForHardwareVideo

### The Chrome Banding Problem — What's Actually Fixable vs Not

| Aspect | Fixable? | How |
|--------|----------|-----|
| vaPutSurface bilinear chroma | **No** — hardcoded in Chromium's VaapiVideoDecoder | Only Vulkan Video decoder replacement would fix this |
| 8-bit YUV→RGB precision | **Partial** — UseMultiPlaneFormatForHardwareVideo helps | But NVIDIA's disable_rgb_to_yuv_conversion limits it |
| Xwayland vs native Wayland | **No difference** — vaPutSurface is before the display backend | Same quality loss on both paths |
| NVIDIA limited RGB range | **Yes** — nvidia-settings → Full range | Check `nvidia-settings -q CurrentColorRange` |
| Switch to Firefox | **Yes** — best quality NVIDIA Linux video | Vulkan Video decode merged June 2026, ships in Firefox 153 (July 2026) |
| `--use-angle=vulkan` or Xwayland | **No** — doesn't fix vaPutSurface | Chromium 129 unblocked it for AMD/Intel but NVIDIA + Wayland still crashes. Xwayland changes the GL backend but vaPutSurface is the same. |

## Chrome Flag Conflicts and GPU Process Crashes

### `--use-gl=egl` Crashes GPU Process

`--use-gl=egl` causes Chrome's GPU process to fail during EGL display initialization on NVIDIA + Wayland. The crash cascades:
1. GPU process fails to boot
2. Chrome disables ALL hardware acceleration (all features go to "Software only")
3. chrome://gpu shows: "GPU process was unable to boot: GPU access is disabled due to frequent crashes"

The only working GL flag on NVIDIA + Wayland is `--use-gl=angle`.

### Feature Flag Conflict — Having Features in Both Enable and Disable

When the same feature appears in both `--enable-features` and `--disable-features`, the **disable list wins**. Chrome treats the disable list as authoritative:
```
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
--disable-features=V...,VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
```
Net result: VAAPI is **disabled** — Video Acceleration Information section in chrome://gpu is completely empty.

### `--enable-features=Vulkan,VulkanFromANGLE,VulkanVideoDecoder` Fails on Wayland

Chrome explicitly errors out:
```
'--ozone-platform=wayland' is not compatible with Vulkan. Consider switching to '--ozone-platform=x11' or disabling Vulkan
Failed to retrieve vkGetInstanceProcAddr pointer from ANGLE.
Failed to create and initialize Vulkan implementation.
```

Vulkan Video decode is **not possible** on Wayland. Video decode must use the VAAPI path.

### Example GPU Report Diagnostic (chrome://gpu)

**Working state (video decode hardware accelerated but empty profile list — missing flags):**
```
Graphics Feature Status:
  Video Decode: Hardware accelerated
  Vulkan: Disabled

Video Acceleration Information:
  Decoding:           ← EMPTY (no profiles listed!)
  Encoding:

Log Messages:
  WARNING: Should skip nVidia device named: nvidia-drm
  ERROR: Wayland not compatible with Vulkan
```

**Broken state (GPU process crash):**
```
Graphics Feature Status:
  Everything: Software only
  GPU process was unable to boot: GPU access is disabled due to frequent crashes.
  
GPU0: VENDOR= 0x0000, DEVICE=0x0000   ← GPU not detected
GL_RENDERER: Disabled
```

## Sources

- Chromium issue #40210909 — vaPutSurface low quality filters: https://issues.chromium.org/issues/40210909
- Chromium issue #349428388 — 10-bit decode not supported: https://issues.chromium.org/issues/349428388
- Chromium issue #447709687 — disable_rgb_to_yuv_conversion on NVIDIA: http://crbug.com/447709687
- Chromium issue #324003973 — Vulkan Video decode feature request: https://issues.chromium.org/issues/324003973
- Khronos Vulkan Video integration design doc: https://www.khronos.org/vulkan/chrome-video/vulkan_video_integration.html
- Phoronix — NVIDIA interested in Vulkan Video for Chrome: https://www.phoronix.com/news/NVIDIA-Vulkan-Video-Chrome-Help
- Slashdot — Firefox merges Vulkan Video decode (June 2026): https://news.slashdot.org/story/26/06/08/1630210/firefox-merges-support-for-vulkan-video-decoding
- Reddit — Firefox Vulkan Video decode discussion: https://www.reddit.com/r/linux/comments/1tz1o0p/it_looks_like_vulkan_video_decode_has_finally/
- NVIDIA Developer Forum — Lack of VA-API / NVDEC issues: https://forums.developer.nvidia.com/t/lack-of-va-api-support-gpu-video-decode-issue-in-chromium-based-browsers/351059
- NVIDIA Developer Forum — VDPAU/VAAPI/NVDEC situation: https://forums.developer.nvidia.com/t/whats-the-situation-with-vdpau-vaapi-nvdec/61031
- elFarto/nvidia-vaapi-driver GitHub: https://github.com/elFarto/nvidia-vaapi-driver
- Arch Linux BBS — Chromium VAAPI discussion (47 pages): https://bbs.archlinux.org/viewtopic.php?id=244031
- Arch Linux BBS — Page 47 NVIDIA working config: https://bbs.archlinux.org/viewtopic.php?id=244031&p=47
- Chrome source — vaapi_wrapper.cc NVIDIA skip: https://chromium.googlesource.com/chromium/src/+/main/media/gpu/vaapi/vaapi_wrapper.cc
- Chrome flag reference: https://peter.sh/experiments/chromium-command-line-switches/
