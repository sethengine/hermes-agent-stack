---
source: 20260801_180255_82edfb
category: gpu
date: 2026-08-01
tags: [kde, kwin, wayland, nvidia, color-profile, srgb, icc, display]
---

# KDE KWin Per-Display Color Profile Source: sRGB (built-in) vs None

On KDE Wayland (KWin), each display has a **color profile source** setting exposed in the per-output config. The relevant key in `~/.config/kwinoutputconfig.json` is `"colorProfileSource"`, which can be `"sRGB"` (the "built-in" preset) or other values.

## What each choice does

| | Built-in `sRGB` | `None` |
|---|---|---|
| Effect | KWin applies a known sRGB transfer curve + primaries to the output | No color transform; raw output to the panel |
| Color-managed apps (browser, GIMP, video) | Render consistently/correctly | Can render off — wrong gamma / oversaturation |
| Standard sRGB panel (e.g. HP X34, `wideColorGamut: false`) | **Correct** | Slightly less accurate for managed content |
| Perf cost | Negligible | None |

## Recommendation for a standard sRGB panel

**Keep `sRGB` (built-in).** For a non-wide-gamut sRGB display (HP X34: `wideColorGamut: false`, confirmed in `kwinoutputconfig.json`), picking `None` gives no benefit and can make color-managed content look wrong. There is no reason to switch on a standard sRGB monitor.

Two edge cases where you would change it:

- **You have a calibrated `.icc` profile** for the panel → load that instead (more accurate than generic sRGB). Set `iccProfilePath` / `hdrIccProfilePath` in `kwinoutputconfig.json`. If `iccProfilePath` is empty, there is nothing to load.
- **Wide-gamut monitor** → `"sRGB"` would clamp/desaturate it; `None` (or a wide-gamut-aware profile) is preferable there. Not applicable to an sRGB panel.

The user's actual config: both HP X34 panels are set to `colorProfileSource: "sRGB"` (connector `DP-3` etc.) — already the correct choice.

## Config location

`~/.config/kwinoutputconfig.json` → per-output object → `colorProfileSource` (`"sRGB"`), `iccProfilePath`, `hdrIccProfilePath`, `wideColorGamut`, `rgbRange`, `hdrColorProfileSource`.

## References
- [[nvidia-wayland-display-color-after-sleep]]
- [[kde-plasma-system-specs]]
- [[wayland-system-specs]]
