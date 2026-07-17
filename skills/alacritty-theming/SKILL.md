---
name: alacritty-theming
description: Create, customize, and switch Alacritty color themes — TOML format reference, color palette design principles, theme switching methods, and pitfalls. Covers the full lifecycle from palette design to live config reload.
category: software-development
triggers:
  - alacritty
  - terminal theme
  - color scheme
  - alacritty config
  - terminal colors
  - theme switcher
  - terminal slow
  - alacritty lag
  - alacritty slow commands
  - terminal typing lag
---

# Alacritty Theming

End-to-end guide for working with Alacritty color themes: designing palettes, writing `.toml` theme files, applying themes, and building switchers.

## Alacritty Theme TOML Format

A theme file has these sections:

```toml
# Primary: background and text colors
[colors.primary]
background = '#1e1e2e'
foreground = '#cdd6f4'

# Cursor colors
[colors.cursor]
text = '#1e1e2e'      # cursor background when typing over selected text
cursor = '#f5e0dc'    # cursor color itself

[colors.vi_mode_cursor]
text = '#1e1e2e'
cursor = '#b4befe'

# Selection highlight
[colors.selection]
background = '#585b70'
text = '#cdd6f4'

# 16 ANSI terminal colors
[colors.normal]
black   = '#45475a'
red     = '#f38ba8'
green   = '#a6e3a1'
yellow  = '#f9e2af'
blue    = '#89b4fa'
magenta = '#f5c2e7'
cyan    = '#94e2d5'
white   = '#bac2de'

[colors.bright]
black   = '#585b70'
red     = '#f38ba8'
green   = '#a6e3a1'
yellow  = '#f9e2af'
blue    = '#89b4fa'
magenta = '#f5c2e7'
cyan    = '#94e2d5'
white   = '#a6adc8'

[colors.dim]  # Optional: dimmed variants (used by some TUI apps)
black   = '#313244'
red     = '#ba5088'
```

### Section reference

| Section | Required | Purpose |
|---------|----------|---------|
| `[colors.primary]` | Yes | Background + foreground |
| `[colors.normal]` | Yes | 8 standard ANSI colors |
| `[colors.bright]` | Yes | 8 bright ANSI colors |
| `[colors.dim]` | No | Dimmed variants (used by some TUI apps) |
| `[colors.cursor]` | Recommended | Cursor foreground + background |
| `[colors.vi_mode_cursor]` | No | Cursor colors when in vi mode |
| `[colors.selection]` | Recommended | Text selection highlight |
| `[colors.search]` | No | Search highlight colors |
| `[colors.hints]` | No | URL hint highlight |
| `[colors.line_indicator]` | No | Line indicator for vi mode |
| `[colors.footer_bar]` | No | Footer bar background |

## Palette Design Principles

### High-contrast text on low-contrast background

The most readable themes use this approach:

- **Background**: dark gray (for dark themes) or medium gray (for light themes), never pure white `#ffffff` or pure black `#000000`
  - Dark gray: `#333333` (basis of low_contrast)
  - Medium gray: `#9a9a9a` to `#b4b4b4`
- **Foreground**: near-black for crisp readability
  - `#141414`, `#181818`, `#1a1c20`, `#1e1e1e`
- **Accent colors**: use exact colors from popular established themes (GitHub Dark, Nord, Catppuccin)
  - Do NOT mute/desaturate them — the user wants "normal" colors that clearly distinguish syntax elements
  - Prefer the "modify only the grays" approach: keep red/green/blue/etc. from a known theme, only adjust foreground, white, bright_white, black

### Color relationships

The `normal` and `bright` rows should be related: `bright_*` is typically a lighter or more saturated version of the matching `normal_*` color. The `dim` row, when present, is a darker/less saturated version.

### Checking contrast ratios

Aim for foreground vs background at least **4.5:1** (WCAG AA) or **7:1** (WCAG AAA). Use online contrast checkers or CLI tools like `colorine`/`wcag-contrast-ratio`.

### Boosting an existing theme (brighter + more intense)

When the user wants an existing theme to be **brighter AND more saturated** — not washed out towards white:

1. **Blending towards white is WRONG** — it desaturates everything (the "faded" look). Don't use it.
2. **Gamma correction** is slightly better but still can't independently boost saturation.
3. **OKLAB color space** is the correct tool: independently boost lightness (L) and chroma (C) while preserving hue.

Workflow:
- Read the original theme (do not modify it)
- Generate 2–3 variant `.toml` files with different L/C combos
- Start aggressive and dial back: prefer starting at L+5% C+4 then reducing chroma if the user says "too vibrant" rather than starting weak and having the user ask for more
- Apply different parameters to background (lightness-only boost, same dc=0 — **never zero out background chroma** or it becomes pure gray)
- Let the user test-swap by changing the `import` line — live reload means instant feedback

Full Python implementation and guidance: `references/oklab-color-boosting.md`

## Adding a Theme

### Manual — edit `alacritty.toml`

```toml
[general]
import = [
    "~/.config/alacritty/themes/themes/my-theme.toml"
]

live_config_reload = true
```

### Path format

Alacritty accepts both forms:
- `~/.config/alacritty/...` (tilde expansion — recommended for config files)
- `/home/user/.config/alacritty/...` (absolute path)

## Live Config Reload

Alacritty watches its config file via inotify (Linux) / FSEvents (macOS). When `live_config_reload = true` (default), any save to `alacritty.toml` applies instantly — no restart needed.

## Switching Methods

### Method 1: Manual

Edit the `import` line to point to a different theme file. Save → instant change.

### Method 2: sed one-liner (for shell aliases)

```zsh
alias alacritty-theme='sed -i "s|\"[^\"]*\.toml\"|\"$HOME/.config/alacritty/themes/themes/$1.toml\"|" ~/.config/alacritty/alacritty.toml'
```

Usage: `alacritty-theme catppuccin_mocha`

### Method 3: Interactive script (pure zsh)

See the `interactive-zsh-scripts` skill's `templates/alacritty-theme-switcher.zsh`.

### Method 4: fzf-powered browser with live-switch

See `interactive-zsh-scripts` skill for fzf integration — `focus:execute-silent` for instant apply, `transform-header` for live/paused toggle, separate helper scripts for subprocess model.

## Critical Pitfalls

### NEVER auto-source interactive scripts from shell rc files

See `interactive-zsh-scripts` skill for the full explanation. TL;DR: it floods your terminal with `%` characters and garbage, tries to launch fzf during shell init, and clobbers configs.

### NEVER modify theme files in a cloned repo — create new files instead

The official `alacritty/alacritty-theme` repo (and most theme collections) are **git repositories**. Modifying files in-place (`low_contrast.toml`, etc.):
- Pollutes `git status` with unexpected changes
- Makes `git pull` conflict-prone
- Destroys the original theme for reference

**Always create a new file** with a different name (e.g. `low_contrast_bright.toml`) for custom variants. The repo is for reference and sync — custom work belongs in separate files.

### Basing custom themes on popular existing themes

When the user asks for a variation of an existing theme:

1. **Leave the original untouched** — read-only, for reference
2. **Create a new file** with a descriptive name (`<original>_<modification>.toml`)
3. **Copy only the colors that should change** from the original where possible
4. **Document what changed** in a comment at the top

Pattern that was well-received: take GitHub Dark's exact accent colors (red, green, blue, yellow, magenta, cyan — normal & bright) and only modify the grays (foreground, white, bright_white) to be brighter and the background to be the user's preferred gray.

### Both `~` and absolute paths work — be consistent

Mixing formats in the same file can confuse grepping for the import path.

## See Also

- `interactive-zsh-scripts` skill — interactive script patterns and fzf integration
- `references/color-design-philosophy.md` — detailed notes on gray-background, muted, high-contrast-text theme design
- `references/oklab-color-boosting.md` — OKLAB L+C boost technique for brighter+more-intense colors (Python code, parameters, pitfalls, dialing-back pattern)
- `references/opencode-themes.md` — creating OpenCode themes that match your Alacritty palette (JSON format, all tokens, community theme sources)
- `references/terminal-rendering-troubleshooting.md` — fixing stale command text, theme reload issues, and font artifacts
- `references/terminal-latency-diagnosis.md` — diagnosing terminal slowness: is it the emulator or the shell? covers zsh startup/keystroke latency, plugin overhead, async tuning, stale compdumps, and dual theme load
