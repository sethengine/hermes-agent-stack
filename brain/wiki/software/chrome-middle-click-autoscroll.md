# Chrome Middle-Click Autoscroll on Linux

**source:** session `20260711_185454_bc366a` (2026-07-11)
**category:** software
**tags:** [chrome, chromium, autoscroll, middle-click, linux, blink-features, google-chrome]

## Problem

Middle-click autoscroll (press scroll wheel, move mouse up/down to scroll) doesn't work on Google Chrome/Chromium on Linux.

## Root Cause

The `MiddleClickAutoscroll` Blink feature is **only enabled on Windows** in the Chromium source code. Linux and macOS have it disabled by default:

```cpp
// enabled only for Windows
if (runtime_flags::isWindows) {
    enableFeature("MiddleClickAutoscroll");
}
```

## Fix

Add `--enable-blink-features=MiddleClickAutoscroll` to all `Exec` lines in Chrome's desktop file at `~/.local/share/applications/google-chrome.desktop`:

```patch
- Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable %U
+ Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable --enable-blink-features=MiddleClickAutoscroll %U

- Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable
+ Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable --enable-blink-features=MiddleClickAutoscroll

- Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable --incognito
+ Exec=env LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct /usr/bin/google-chrome-stable --incognito --enable-blink-features=MiddleClickAutoscroll
```

## Caveat

On Linux, middle-click normally performs **paste** (X primary selection). On Wayland (KDE Plasma), this may conflict with Chrome's autoscroll behavior since both bind to the middle-click button. If conflicts arise, `keyd` can be used to remap middle-click behavior per-application.
