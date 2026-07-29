# Chrome GPU Flags + Screen Blanking Issues — Case Reference

## System Profile
- Distro: Manjaro Linux (rolling), kernel 7.0.10-1-MANJARO
- GPU: NVIDIA RTX 5060 Ti (GB206/Blackwell), driver 595.71.05
- Display: HP X34 34" 3440x1440@165Hz ultrawide (FreeSync)
- Session: Wayland, KDE Plasma 6.6.5 / KWin 6.6.5
- Chrome: 149.0.7827.53 (launched via `google-chrome-stable` Arch wrapper)
- CPU: Intel Core Ultra 7 265K (Arrow Lake, 20C/20T)

## Chrome GPU Flag Diagnosis (June 2026)

### Broken Configuration Found
```
~/.config/chrome-flags.conf contained:
--ozone-platform=wayland
--use-gl=angle                                ← NO backend specified
--ignore-gpu-blocklist
--enable-gpu-rasterization
--enable-native-gpu-memory-buffers            ← Harmful on NVIDIA Wayland
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
--num-raster-threads=10
```

### Root Cause
`--use-gl=angle` without `--use-angle=vulkan` causes Chrome's ANGLE to default to **SwiftShader** (software rendering) on this configuration. WebGL, Canvas, and GPU rasterization silently run on CPU.

### Fix Applied
Changed to `--use-gl=angle --use-angle=vulkan` (or alternatively `--use-gl=desktop` for native OpenGL path). Also added `--disable-gpu-driver-bug-workarounds` and removed `--enable-native-gpu-memory-buffers`.

### Verification
Opening `chrome://gpu` should show:
- Canvas: Hardware accelerated
- WebGL: Hardware accelerated
- Rasterization: GPU rasterization enabled
- SwiftShader: Not present

## Screen Blanking / Display Wake Failure (June 2026)

### Symptom
- Monitor LED shows signal (ON/active)
- Screen stays black
- Pressing any key causes keyboard backlight to flash briefly (USB resumes), then goes dark again
- Neither mouse nor keyboard can wake the display

### Root Cause Chain
```
1. powerdevilrc: TurnOffDisplayIdleTimeoutSec=300   → screen blanks after 5 min idle
2. powerdevilrc: IgnoreIdleInhibitors=true           → Steam/Chrome "playing game" blocks are ignored
3. PowerDevil: "Watching for DPMS state changes unimplemented" → Can't track blank/unblank transitions
4. powermanagementprofilesrc: AutoSuspendIdleTimeoutSec=3600 → System tries S3 suspend after 1 hour
5. HP X34 (FreeSync): Scaler renegotiation on wake fails with NVIDIA
= Broken DPMS monitoring + attempted suspend + monitor link renegotiation failure = permanent black screen
```

### Key Log Line
```
org_kde_powerdevil[1781]: Watching for DPMS state changes unimplemented
```

### Fix Applied
```bash
kwriteconfig6 --file powermanagementprofilesrc --group AC --group SuspendAndShutdown --key AutoSuspendIdleTimeoutSec 0
kwriteconfig6 --file powerdevilrc --group AC --group Display --key TurnOffDisplayIdleTimeoutSec 0
systemctl --user restart plasma-powerdevil
```

Also useful to know: the D-Bus PolicyAgent path for KDE 6 is:
```
/org/kde/Solid/PowerManagement/PolicyAgent
org.kde.Solid.PowerManagement.PolicyAgent.AddInhibition(uint types, QString app_name, QString reason)
```
Types bitmask: 1=logout, 2=suspend, 4=screen off. Use 6 for suspend + screen off.

### Env Vars Found to Be Present (not necessarily harmful but worth noting)
- `__GL_YIELD=USLEEP` — historical yield strategy; may cause micro-stutter on driver 595 Wayland
- `KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1` — disables KWin's NVIDIA triple buffering (can reduce smoothness)
- `KWIN_TRIPLE_BUFFER=0` — KDE5 relic, no effect on KDE6
- `__GL_VRR_ALLOWED=1` — allows VRR signals (good)
- `__GL_SYNC_TO_VBLANK=0` — vsync off (correct for VRR)
- `usbhid.mousepoll=1 usbhid.kbpoll=1` — kernel cmdline, sets USB HID to 1000 Hz polling
