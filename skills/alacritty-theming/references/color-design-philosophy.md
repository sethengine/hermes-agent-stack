# Color Design Philosophy for Terminal Themes

Design notes from the user's preferences, derived from multiple iterations of custom Alacritty theme creation.

## Core Preferences (confirmed by iteration)

1. **Gray background** — not white, not dark. True neutral gray.
   - For dark themes: `#333333` (like the original `low_contrast` theme)
   - For medium gray: `#9a9a9a` (concrete) to `#b4b4b4` (pumice)
   - Avoid pure white `#ffffff`, near-white `#f8f8f8`, or anything below `#7a7a7a`

2. **High-contrast text** — foreground must pop against the background
   - On dark bg (#333333): `#eeeeee` — NOT a muted gray like `#dddddd`
   - On medium gray bg: `#141414` to `#181818` — near-black
   - The bg/fg contrast ratio should be above 10:1 if possible, at minimum 6:1

3. **Accent colors must be "normal" saturated colors — NOT pastel, NOT muted**
   - Pastel/desaturated accents make syntax elements indistinguishable
   - Use exact colors from a well-known established theme as the base
   - **The confirmed-working pattern: "exact popular-theme colors, modify only the grays"**

## The Confirmed-Working Pattern: "Exact Colors, Modify Only Grays"

This approach was validated across multiple iterations and is the preferred method:

1. **Pick a source theme** that has well-known, well-balanced accent colors (GitHub Dark, Nord, Catppuccin, etc.)
2. **Copy all accent colors exactly** (red, green, yellow, blue, magenta, cyan — both normal and bright variants)
3. **Modify only the neutral/grayscale values:**
   - `background` — set to the user's preferred gray
   - `foreground` — set to a bright/high-contrast value
   - `white` / `bright_white` — adjust to be brighter than the source theme
   - `black` / `bright_black` — keep from source theme or adjust slightly
4. **Leave everything else untouched**

### Concrete example: low_contrast_bright

The theme that was well-received:

| Value | GitHub Dark | low_contrast_bright |
|-------|------------|-------------------|
| **red** | `#ea4a5a` | **same** `#ea4a5a` |
| **green** | `#34d058` | **same** `#34d058` |
| **yellow** | `#ffea7f` | **same** `#ffea7f` |
| **blue** | `#2188ff` | **same** `#2188ff` |
| **magenta** | `#b392f0` | **same** `#b392f0` |
| **cyan** | `#39c5cf` | **same** `#39c5cf` |
| **foreground** | `#d1d5da` | **→ `#eeeeee`** (much brighter) |
| **white** | `#d1d5da` | **→ `#e0e0e0`** |
| **bright_white** | `#fafbfc` | **→ `#ffffff`** |
| **background** | `#24292e` | **→ `#333333`** |

All other colors (black, bright_black, bright_red, bright_green, etc.): **identical to GitHub Dark**.

The diff from GitHub Dark is exactly 4 lines changed out of 20+ color values.

### Why this works

- The accent colors are **instantly recognizable** and properly distinct — no iteration needed
- The gray modifications solve the specific problem: "hard to read text against dark background"
- The user can describe what they want in one sentence: "GitHub Dark colors but with brighter text on a #333333 background"
- Total iteration time: one attempt instead of 5+

## Dark-Theme Variant (Alternative: Gray Background with Dark Base)

For themes based on `low_contrast`'s `#333333` background with bright foreground:

- The background is dark enough that the user doesn't want desaturated colors — saturated accents are needed for readability
- The "muted everything" approach was rejected for dark themes because all colors blurred together
- The sweet spot: dark gray background (#333333), bright foreground (#eeeeee), normally-saturated accent colors from a known palette

## Alternative Approach (Historical — was not preferred by this user)

### Muted palette on medium gray (#9a9a9a) background

For a fully muted, low-contrast-overall theme (rejected by the user who prefers "normal" saturated accents):

| Color | Hex | Saturation | Notes |
|-------|-----|-----------|-------|
| black | `#2a2a2a` | 0% | Near-gray |
| red | `#7a4a4a` | ~25% | Brick, not fire |
| green | `#4a6a4a` | ~20% | Moss, not emerald |
| yellow | `#6a5a3a` | ~25% | Ochre, not gold |
| blue | `#4a5a7a` | ~25% | Slate, not ocean |
| magenta | `#6a4a6a` | ~20% | Mauve, not plum |
| cyan | `#4a6a6a` | ~20% | Teal, not cyan |
| white | `#b0b0b0` | 0% | Just lighter gray |

These all sit in the `#4a-#7a` range for lightness — none dominates visually. Colors with any RGB channel at 0 or 255, or with saturation (max-min) > 150, are too vibrant for this approach.

This may be useful for future users who specifically request a "fully muted" theme, but is NOT the default preference.

## Adding Custom Themes to the Repo

**CRITICAL: Always create a new file, never modify an original theme.**

When the user asks for a variation of an existing theme:
1. Read the original theme file (read-only, for reference)
2. Create a new file with a descriptive name: `<original>_<modification>.toml`
3. Copy colors from the original, changing only what's requested
4. Add a comment at the top documenting what changed
5. Never run `git checkout` to restore — that shouldn't be needed if you never modified it
