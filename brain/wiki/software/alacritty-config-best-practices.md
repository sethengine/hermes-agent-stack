---
source_session: 20260601_164712_ab05bd
extracted_date: 2026-07-17
category: software-development
tags: [alacritty, terminal, configuration, nerd-fonts]
---

# Alacritty Configuration Essentials

Key settings for an optimal Alacritty 0.17+ setup (from ricing a Manjaro KDE Wayland install):

## TERM environment

Change `TERM = "xterm-256color"` to `TERM = "alacritty"` for proper true-color (24-bit) and italics support. Ensure the terminfo entry is installed (`tic -sx` if missing).

```toml
[env]
TERM = "alacritty"
```

## Nerd Font

SF Mono lacks icon glyphs for Starship/Powerlevel10k/Neovim web-devicons. Use a Nerd Font:

```toml
[font]
normal = { family = "JetBrainsMono Nerd Font", style = "Regular" }
```

## Visual polish

```toml
[window]
opacity = 0.95
padding = { x = 12, y = 12 }
dynamic_padding = true
decorations = "None"       # blends cleanly with KDE tiling

[cursor]
style = "Beam"
blinking = "On"
```

## Font size keybindings

```toml
[[keyboard.bindings]]
key = "Plus"
mods = "Control|Shift"
action = "IncreaseFontSize"
```

## Theme import

Themes from [[alacritty-theme-repo]] live at `~/.config/alacritty/themes/themes/`. Import via:

```toml
import = ["~/.config/alacritty/themes/themes/oxocarbon.toml"]
```

See [[alacritty-theme-switcher-fzf]] for interactive theme browsing.
