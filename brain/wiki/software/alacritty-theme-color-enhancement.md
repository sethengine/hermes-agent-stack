---
source_session: 20260607_125419_d10775
extracted: 2026-07-17
category: software
tags: [alacritty, theming, colors, oklab, oklch]
---

# Alacritty Theme Color Enhancement

## OKLAB/OKLCH for Perceptual Color Boosting

Blending Alacritty theme colors towards white (HSL) desaturates and fades them. The correct approach is to use **OKLAB/OKLCH** color space, which separates lightness and chroma (intensity) independently:

- Boost **lightness (L)** to make text brighter (e.g., L+5%)
- Boost **chroma (C)** to make colors more intense (e.g., C+2–4)
- Keep background chroma at zero for neutral lightness-only boost
- Use `colour` Python library: `colour.Color` with OKLAB conversion

### Methods Compared

| Method | Effect | Issue |
|--------|--------|-------|
| HSL blend towards white | Brighter but faded | Desaturates colors |
| Gamma curve (0.45–0.55) | Natural lift | Mid-tones only |
| Linear blend (%) | Uniform boost | Washes out |
| **OKLAB L+C** | Brighter AND intense | Best result |

## zsh-syntax-highlighting Plugin Order Fix

Stale/cancelled command text reappearing in Alacritty is caused by `zsh-syntax-highlighting` not being last in the plugin load order. It hooks `zle-line-pre-redraw` — plugins loaded after it overwrite its hooks, causing stale buffer text to bleed through.

**Fix:** Load `zsh-syntax-highlighting` as the **last** plugin.

## Powerlevel10k Prompt Arrow Color

The `❯` arrow at the start of the prompt is `POWERLEVEL9K_PROMPT_CHAR_OK_VIINS_FOREGROUND` (success, default green 76) and `POWERLEVEL9K_PROMPT_CHAR_ERROR_VIINS_FOREGROUND` (error, red 196).

## Alacritty Live Reload

`live_config_reload = true` in Alacritty config applies theme changes instantly without restart.
