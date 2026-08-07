---
session: 20260613_180504_d7f8db
date: 2026-06-13
category: software
tags: [chrome, css, theming, light-gray, browser-config, stylus]
---

# Chrome Light Gray Background Setup

Chrome has **no built-in flag or CLI option** to replace white backgrounds with a custom light gray. The `#enable-force-dark` flag and `WebContentsForceDark` feature only do dark-mode inversion (white→black), not white→gray.

**Best solution: Stylus extension with global CSS rule**

```css
html { background-color: #d9d9d9 !important; }
```

Apply to "On all sites" for universal coverage. No whitelisting needed.

**Alternative: Dark Reader in "Light" theme mode** — actively replaces `#fff` with a configurable gray via the "Background" slider.

**No-extension options:**
- `--enable-features=WebContentsForceDark` with any variant (`hsl_based`, `cielab_based`, `rgb_based`) cannot tune target color — only determines which elements invert
- `--blink-settings` approach also fails for custom gray

Other notable CSS: `* { background-color: #e8e8e8 !important; }` with `color: #1a1a1a` for text and `#0044cc` for links.

## References
