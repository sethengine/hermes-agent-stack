# OKLAB Color Boosting for Terminal Themes

How to make an existing theme's colors **brighter AND more intense** (not just washed out towards white). Developed while customizing TokyoNight Night for higher contrast.

## The Problem: Blending Towards White = Faded

Naively blending each color towards `#ffffff` (blending towards white) **reduces saturation**. The blues become pastel, the reds become pink — the user described this as "faded." This is because:
- RGB linear interpolation towards the white point simultaneously increases L and decreases chroma
- For colors already at moderate-to-high lightness, the result is washed out

| Color | Original | 40% towards white | Result |
|-------|----------|-------------------|--------|
| Red `#f7768e` | Saturated | `#faacbb` | Pale/faded |
| Green `#9ece6a` | Medium sat. | `#c4e1a5` | Washed out |
| Blue `#7aa2f7` | Medium sat. | `#afc7fa` | Desaturated |

Gamma correction (`new = 255 * (old/255)^power`) is slightly better — it preserves mid-tone saturation — but still doesn't independently control saturation.

## The Solution: OKLAB Lightness + Chroma Boost

OKLAB (Björn Ottosson 2021) is a perceptually uniform color space that cleanly separates:
- **L** (lightness) — how bright the color appears
- **a/b** (opponent axes) — convert to OKLCH for chroma + hue
- **C** (chroma) — how intense/saturated the color is
- **H** (hue) — what color it is

You can independently add to L (more lightness) and C (more saturation) without affecting the hue. This produces colors that are **both brighter AND more vivid**.

### Python Implementation

```python
import math

def hex_to_rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i+2], 16)/255 for i in (0, 2, 4)]

def rgb_to_hex(rgb):
    r = max(0, min(255, int(rgb[0]*255 + 0.5)))
    g = max(0, min(255, int(rgb[1]*255 + 0.5)))
    b = max(0, min(255, int(rgb[2]*255 + 0.5)))
    return f'#{r:02x}{g:02x}{b:02x}'

def linearize(c):
    return c/12.92 if c <= 0.04045 else ((c + 0.055)/1.055)**2.4

def delinearize(c):
    return 12.92*c if c <= 0.0031308 else 1.055*c**(1/2.4) - 0.055

def rgb_to_oklab(rgb):
    r, g, b = [linearize(c) for c in rgb]
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l = l**(1/3); m = m**(1/3); s = s**(1/3)
    return [0.2104542553*l + 0.7936177850*m - 0.0040720468*s,
            1.9779984951*l - 2.4285922050*m + 0.4505937099*s,
            0.0259040371*l + 0.7827717662*m - 0.8086757660*s]

def oklab_to_rgb(lab):
    l = lab[0] + 0.3963377774*lab[1] + 0.2158037573*lab[2]
    m = lab[0] - 0.1055613458*lab[1] - 0.0638541728*lab[2]
    s = lab[0] - 0.0894841775*lab[1] - 1.2914855480*lab[2]
    l = l**3; m = m**3; s = s**3
    return [delinearize(c) for c in [
        4.0767416621*l - 3.3077115913*m + 0.2309699292*s,
       -1.2684380046*l + 2.6097574011*m - 0.3413193965*s,
       -0.0041960863*l - 0.7034186147*m + 1.7076147010*s,
    ]]

def boost_color(hex_color, dl=0, dc=0):
    """Boost OKLAB lightness by dl and chroma by dc."""
    rgb = hex_to_rgb(hex_color)
    lab = rgb_to_oklab(rgb)
    a, b = lab[1], lab[2]
    chroma = math.hypot(a, b)
    hue = math.atan2(b, a)
    new_L = max(0, min(1, lab[0] + dl))
    new_C = max(0, chroma + dc)
    new_lab = [new_L, new_C * math.cos(hue), new_C * math.sin(hue)]
    return rgb_to_hex(oklab_to_rgb(new_lab))
```

### Recommended Starting Parameters

| Label | dl (lightness) | dc (chroma) | Effect |
|-------|---------------|-------------|--------|
| Balanced | +0.03 (3%) | +0.03 | Most natural — "L+3%, C+3" |
| Lighter fg | +0.04 (4%) | +0.02 | Foreground pops more, slightly less saturated accents |
| Most intense | +0.03 (3%) | +0.04 | Colors really pop (green/yellow may clip near pure) |
| **Bright + dialed** | **+0.05 (5%)** | **+0.02** | **Best for legibility — bright text with restrained saturation** |

The **L+5%, C+2** combo emerged as the sweet spot for readability: text gets a noticeable lightness bump while chroma is dialed back enough that green/yellow don't clip to pure neon. Start here when the user wants "brighter, easier to read, not washed out."

### Dialing Back

Users may say "too vibrant" after the first attempt. The fix is to **reduce chroma only while keeping lightness**. This preserves readability while taming saturation:

1. Start with an aggressive guess (e.g. L+5%, C+4)
2. If user says "too vibrant / too intense": reduce dc by 0.02 → C+2, keep dl unchanged
3. If user says "too washed out / faded": increase dc by 0.01-0.02, keep dl unchanged
4. Never drop dl below +0.03 for text colors or the brightness gain will be imperceptible

### Handling the Background

The background color should **not** get the same chroma boost (it has near-zero chroma anyway, and boosting it can introduce a color cast). Apply only a small lightness boost:

```python
background_boosted = boost_color('#1a1b26', dl=0.03, dc=0.0)
```

Typical result: `#1a1b26` → `#1f203b` — still dark, but slightly less oppressive. Adjust `dl` to taste (0.02–0.04 range).

**CRITICAL: Preserve the original background's cast — don't zero out chroma.** Setting background chroma to zero (pure gray) may seem correct, but users notice immediately. The original `#1a1b26` has a subtle blueish tint (B channel higher than R/G). If you set `new_C = 0` in OKLAB, the result is `#232323` (pure gray) — the user will call this out. Instead, apply only the lightness boost with `dc=0` (keeping original chroma).

Bad: `neutralize_bg=True` → pure gray `#232323` → user says "make it blueish like before"
Good: `dc=0` → `#21222d` (same blue tint, just lighter) → user is happy

## Full Theme Example: Transforming a TOML File

```python
import re

def transform_toml(content, dl, dc, bg_dl):
    """Apply OKLAB boost to all hex colors in a TOML theme."""
    def replace_hex(m):
        hx = m.group(1)
        # Background gets only lightness boost
        if hx == '1a1b26':  # or whatever the original bg is
            new = boost_color(hx, bg_dl, 0)
        else:
            new = boost_color(hx, dl, dc)
        return f"'{new}'"
    return re.sub(r"'#([0-9a-fA-F]{6})'", replace_hex, content)
```

### Workflow

1. **Read the original theme** — do not modify it
2. **Generate 2-3 variant files** with different dl/dc combos as separate `.toml` files
3. **Name descriptively**: `tokyonight_night_oklab_l3c3.toml`, etc.
4. **Let the user test-swap** by changing Alacritty's `import` line — live config reload means instant switching
5. **Remove weak/v0 variants** once better ones are generated (don't leave orphans)

## Pitfalls

- **CLIPPING** at extreme boosts: chroma values that exceed the sRGB gamut will clip to `rgb(0)` or `rgb(255)`, losing detail. The `max(0, min(255, ...))` clamp in `rgb_to_hex` catches this silently — but check the output for values at exactly `#00` or `#ff` on the non-dominant channels, which means clipping.
- **Bright yellow/green at C+4**: `#9fe044` (bright green) at +4 chroma becomes `#9fee00` — near-pure green. That might feel too harsh. Dial chroma back (C+3) for these, or accept it as the user's preference for "intense."
- **Background chroma boost is wrong**: Never boost background chroma significantly — even `dc=0.01` on a near-neutral `#1a1b26` can push it subtly blue or purple. Always use `dc=0` for background.
- **Blending-approach timidity**: The first attempt should show **visible** changes. The user instantly notices when 12% towards white barely budges a color. Compute the delta per channel and ensure it's ≥ 10 on at least one channel for mid-tones.
- **Don't gamma-brighten as a substitute for OKLAB**: Gamma correction (`new = 255 * (old/255)^power`) lifts mid-tones but doesn't boost chroma. It's better than naive white-blend but worse than full OKLAB.

## Comparison with Other Methods

| Method | Brighter? | More saturated? | Preserves hue? | Perceptually uniform? |
|--------|-----------|----------------|----------------|----------------------|
| White blending | Yes | No (desaturates) | Approx. | No |
| Gamma power curve | Yes | Mid-tones OK | Yes | No |
| HSL L+saturation boost | Yes | Yes | Yes | No (H≠H is inconsistent) |
| **OKLAB L+chroma boost** | **Yes** | **Yes** | **Yes** | **Yes** |
