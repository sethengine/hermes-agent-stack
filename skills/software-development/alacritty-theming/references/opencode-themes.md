# OpenCode Theme Creation (matching an Alacritty palette)

OpenCode (opencode.ai) uses a JSON-based theme format, separate from Alacritty's TOML. This reference covers how to create an OpenCode theme that matches a given Alacritty terminal theme.

## Theme File Location

User-wide themes go in `~/.config/opencode/themes/*.json`. Project-specific themes in `.opencode/themes/*.json`.

## Theme Structure

```json
{
  "$schema": "https://opencode.ai/theme.json",
  "defs": {
    "myColor": "#ff6600"
  },
  "theme": {
    "tokenName": {
      "dark": "myColor",
      "light": "#ff6600"
    }
  }
}
```

Colors can be:
- Hex: `"#ff6600"`
- Reference to `defs`: `"myColor"`
- ANSI index: `3` (integer 0-255)
- Terminal default: `"none"`

Use `"dark"`/`"light"` variants for adaptive themes, or a single string `"#fff"` for fixed.

## Full Theme Token Reference

### UI Tokens (controls the OpenCode interface)

| Token | Purpose | Suggested mapping from Alacritty |
|-------|---------|----------------------------------|
| `primary` | Brand/action color, links, buttons | Alacritty `blue` |
| `secondary` | Less prominent accent | Alacritty `cyan` |
| `accent` | Highlight, focus indicators | Alacritty `magenta` or `cyan` |
| `error` | Errors, failures | Alacritty `red` |
| `warning` | Warnings | Alacritty `yellow` |
| `success` | Success messages, completions | Alacritty `green` |
| `info` | Informational | Alacritty `blue` or `cyan` |
| `text` | Primary text | Alacritty `foreground` |
| `textMuted` | Secondary/less important text | Mid-point between foreground and background |
| `background` | Main background | Alacritty `background` |
| `backgroundPanel` | Panel/card background | Slightly lighter than `background` |
| `backgroundElement` | Input fields, list items | Slightly lighter than `backgroundPanel` |
| `border` | Default border | Mid-gray |
| `borderActive` | Focused/active border | Alacritty `blue` |
| `borderSubtle` | Subtle dividers | Slightly darker than `backgroundPanel` |

### Diff Tokens

| Token | Suggested |
|-------|-----------|
| `diffAdded` | Alacritty `green` |
| `diffRemoved` | Alacritty `red` |
| `diffContext` | Alacritty `bright_black` or `black` |
| `diffHighlightAdded` | Alacritty `bright_green` |
| `diffHighlightRemoved` | Alacritty `bright_red` |
| `diffAddedBg` | Subtle green-tinted version of `background` |
| `diffRemovedBg` | Subtle red-tinted version of `background` |

### Markdown Tokens

| Token | Suggested |
|-------|-----------|
| `markdownText` | `foreground` |
| `markdownHeading` | `primary` (blue) |
| `markdownLink` | `secondary` or `blue` |
| `markdownCode` | `green` |
| `markdownBlockQuote` | `border` or `textMuted` |
| `markdownEmph` / `markdownStrong` | `yellow` |
| `markdownListItem` | `primary` |
| `markdownCodeBlock` | `foreground` |

### Syntax Highlighting Tokens

| Token | What it colors | Suggested |
|-------|---------------|-----------|
| `syntaxComment` | Comments | `bright_black` (muted) |
| `syntaxKeyword` | Keywords (if, for, return, class) | `magenta` or `blue` |
| `syntaxFunction` | Function/method names | `blue` |
| `syntaxVariable` | Variables, identifiers | `cyan` |
| `syntaxString` | String literals | `green` |
| `syntaxNumber` | Numeric literals | `magenta` or `green` |
| `syntaxType` | Types, class names | `cyan` or `yellow` |
| `syntaxOperator` | Operators (=, +, -, etc.) | `blue` or `foreground` |
| `syntaxPunctuation` | Brackets, commas, semicolons | `foreground` |

## Complete Example (low_contrast_bright)

The full theme at `~/.config/opencode/themes/low-contrast-bright.json` maps these Alacritty colors:
- bg `#333333`, fg `#eeeeee`
- GitHub Dark accent colors (red `#ea4a5a`, green `#34d058`, blue `#2188ff`, etc.)
- All 40+ theme tokens defined with dark-only variants

See the file at `~/.config/opencode/themes/low-contrast-bright.json` for the complete reference implementation.

## Community Themes

The largest collection is at `github.com/scaryrawr/base16-opencode` — 490+ base16/base24 themes. Install:

```bash
mkdir -p ~/.config/opencode/themes
cd ~/.config/opencode/themes
git clone https://github.com/scaryrawr/base16-opencode.git base16
# Symlink so OpenCode finds them:
ln -s base16/themes/*.json .
```

Available themes include: base16 variants of tokyonight, catppuccin, gruvbox, dracula, nord, ayu, everforest, and 480+ more.

## Switching Themes

In the OpenCode TUI: type `/theme <name>` and tab-complete.

For permanent setting, add to `~/.config/opencode/tui.json`:
```json
{
  "theme": "low-contrast-bright"
}
```

The `system` theme (built-in) adapts to your terminal's ANSI colors automatically.
