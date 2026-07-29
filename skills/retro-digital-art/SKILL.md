---
name: retro-digital-art
description: "Create retro and text-based digital art: ASCII banners, ASCII video, and pixel art with era-accurate palettes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, ascii-art, pixel-art, retro, text-art, video, generative-art]
---

# Retro Digital Art

Generate text-based and retro-styled visual art.

---

## ASCII Art

Render text as large ASCII banners using pyfiglet (571 fonts), cowsay, and boxes.

```bash
pip install pyfiglet --break-system-packages -q
python3 -m pyfiglet "YOUR TEXT" -f slant
python3 -m pyfiglet --list_fonts
```

Recommended fonts: `slant` (clean), `doom` (bold), `big` (readable), `cyberlarge` (tech).

**Full docs:** See `references/ascii-art/SKILL.md`.

---

## ASCII Video

Convert video/audio to colored ASCII MP4/GIF with real-time effects and shaders.

**Full docs, effects, shaders, and optimization notes:** See `references/ascii-video/SKILL.md` and `references/ascii-video/`.

---

## Pixel Art

Convert images into retro pixel art with era-accurate palettes (NES, Game Boy, PICO-8, C64, arcade, SNES) and animate them into looping MP4/GIF.

Scripts:
- `references/pixel-art/scripts/pixel_art.py` — photo → pixel-art PNG
- `references/pixel-art/scripts/pixel_art_video.py` — pixel-art PNG → animated MP4/GIF

**Full docs:** See `references/pixel-art/SKILL.md` and `references/pixel-art/`.
