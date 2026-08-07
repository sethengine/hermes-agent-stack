---
title: "Alacritty Does Not Support Text Shadows"
category: software
source_session: 20260601_174247_265b06
created: 2025-07-29
tags: [alacritty, terminal-emulator, text-rendering, gpu, opengl]
related_wiki: [software/terminal-emulators, software/kde-plasma-compositor]
---

# Alacritty: No Text Shadow Support

**Alacritty does not support text shadows** (glow, drop shadow, or any glyph-level shadow effect). This is a confirmed limitation:

- Feature was [requested in 2017](https://github.com/jwilm/alacritty/issues/730) but never implemented.
- Alacritty renders text directly via its GPU renderer ([[OpenGL]]/[[Vulkan]]), not through a CSS or browser-style layout engine. Adding text shadows would require non-trivial changes to the rendering pipeline.
- There is no `shadow` or equivalent option in any section of the [[alacritty-toml-config]] — not under `colors`, `font`, `window`, or `render`.

## What Alacritty Does Support Visually

- `window.opacity` — background transparency (0.0–1.0)
- `window.blur` — background blur behind transparent windows (KDE Wayland / macOS)
- `window.decorations` — toggle window borders / titlebar

## Alternatives

- **Window drop shadows** — handled by the [[kde-plasma]] compositor (KWin), not the terminal. Configure via System Settings > Window Decorations > Shadow settings, or per-app KWin rules.
- **Text glow/shadow effects** — not available in any mainstream terminal emulator. Options include custom-configured [[kitty-terminal]] with compositor hacks, or using a non-terminal application entirely.
- **Compositor-level text effects** — KDE's KWin does not expose per-glyph shadow effects. For true text shadows, a custom rendering engine or a GTK/Qt widget overlay would be needed.
