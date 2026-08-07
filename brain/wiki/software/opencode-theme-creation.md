---
source_session: 20260601_164712_ab05bd
extracted_date: 2026-07-17
category: software-development
tags: [opencode, themes, json, color-schemes, cursor]
---

# OpenCode Theme Creation

OpenCode themes are JSON files with 50+ token definitions for every UI element. They live in `~/.config/opencode/themes/`.

## Theme downloads

A collection of 490 base16/base24 themes was downloaded from the [[base16-opencode-repo]]:
```bash
git clone https://github.com/scaryrawr/base16-opencode.git
cp -r base16-opencode/themes/* ~/.config/opencode/themes/
```

## Porting Alacritty palettes

When creating an OpenCode theme from an [[alacritty-custom-theme-creation]] palette:

- **darkBg** → Alacritty `background`
- **darkFg** → Alacritty `foreground`
- **darkPanel/darkElement** → slightly lighter/darker bg variants
- **syntax tokens** → map normal/bright colors for keywords, strings, comments, etc.
- **diff backgrounds** → map green (additions) and red (deletions)

## Cursor theme brightening

The built-in `cursor` theme was brightened 20% (backgrounds only) at `~/.config/opencode/themes/cursor-bright.json`:

```json
{ "theme": "cursor-bright" }
```

Use in OpenCode via `/theme cursor-bright` or set permanently in `~/.config/opencode/tui.json`:

```json
{ "$schema": "https://opencode.ai/tui.json", "theme": "low-contrast-bright" }
```

Themes apply immediately — no restart needed.
