# OpenCode Terminal Integration: Clickable Links

OpenCode renders markdown links with ANSI visual styling (underline/color) but does NOT emit OSC 8 hyperlink escape sequences (`\e]8;;URL\e\\...`). This means links *look* clickable but are not. Fix this at the terminal emulator level.

## The Problem

| Rendering | OpenCode? | Clickable? |
|-----------|-----------|------------|
| ANSI SGR (underline + color) | Yes — TUI mode | No |
| Raw markdown `[text](url)` | Yes — `run` mode | No |
| OSC 8 `\e]8;;URL\e\\...` | No — not emitted | Yes |

## Solution: Alacritty Hints (Regex-Based URL Detection)

Alacritty's hint system uses regex to detect URLs in terminal output and makes them actionable via keyboard (`Ctrl+Shift+U`) or mouse (`Ctrl+Click`).

### Config (`~/.config/alacritty/alacritty.toml`)

```toml
[hints]
enabled = [
  # Universal URL matcher — works for plain URLs AND URLs inside markdown [text](url)
  # The regex starts at https?:// and stops at whitespace, ), ], ', ", <, >
  { regex = "https?://[^\\s)'\"<>\\]\\[]+", command = "/home/USER/.local/bin/alacritty-hint-open", post_processing = true, mouse = { enabled = true, mods = "Control" } },
  # GitHub refs: owner/repo#123
  { regex = "[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+#\\d+", command = "/home/USER/.local/bin/alacritty-hint-open", post_processing = true, mouse = { enabled = true, mods = "Control" } },
  # arxiv IDs: 2402.03300
  { regex = "\\d{4}\\.\\d{4,5}", command = "/home/USER/.local/bin/alacritty-hint-open", post_processing = true, mouse = { enabled = true, mods = "Control" } },
]
```

**Important**: Do NOT add `url = { modifiers = "Control" }` under `[mouse]` — this key was removed in Alacritty 0.13. Using it logs `Unused config key: url` (WARN). Mouse URL handling is now per-hint via the `mouse` field inside each hint definition.

### Pitfall: `action = "Open"` Does Not Exist

Alacritty hints support only these `action` variants: `Copy`, `Paste`, `Select`, `MoveViModeCursor`. To open a URL, you MUST use `command = "xdg-open"` or a wrapper, not `action = "Open"`. An invalid action variant causes a config parse error: `unknown variant Open, expected one of copy paste select movevimodecursor`.

### Pitfall: `\b` Word Boundaries Break Regex Compilation

Alacritty uses the Rust `regex` crate's DFA engine which does NOT support Unicode word boundaries. Using `\b` in a hint regex produces: `could not compile hint regex: unsupported regex feature for DFAs: cannot build lazy DFAs for regexes with Unicode word boundaries`. Solution: remove `\b` — patterns like `\d{4}\.\d{4,5}` are specific enough without them.

### Pitfall: TUI Mouse Reporting Blocks Ctrl+Click

OpenCode's TUI (and many other terminal apps: vim, htop, btop, lazygit) enable **mouse reporting** (SGR/X10 mouse mode) to handle clicks within their UI. When mouse reporting is active, the terminal emulator forwards ALL click events to the application — Alacritty's hint-level `mouse` config cannot intercept them. **Ctrl+Click on hints will silently fail.**

The reliable workaround is keyboard hint mode: **Ctrl+Shift+U** enters hint mode independently of mouse reporting, overlaying numbered labels on all detected URLs. Type to filter, press the label key to open. This always works regardless of application mouse mode.

### Wrapper Script (`~/.local/bin/alacritty-hint-open`)

`xdg-open` alone can't handle GitHub refs (`owner/repo#123`) or arXiv IDs (`2402.03300`). A wrapper expands non-URL matches to full URLs:

```bash
#!/usr/bin/env bash
text="$1"

# Already a URL
if [[ "$text" =~ ^https?:// ]]; then
    exec xdg-open "$text"
fi

# GitHub ref: owner/repo#123 → https://github.com/owner/repo/issues/123
if [[ "$text" =~ ^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+#[0-9]+$ ]]; then
    repo="${text%#*}"
    issue="${text#*#}"
    exec xdg-open "https://github.com/${repo}/issues/${issue}"
fi

# arXiv ID: YYYY.NNNNN → https://arxiv.org/abs/YYY.NNNNN
if [[ "$text" =~ ^[0-9]{4}\.[0-9]{4,5}$ ]]; then
    exec xdg-open "https://arxiv.org/abs/${text}"
fi

exec xdg-open "$text"
```

Make executable: `chmod +x ~/.local/bin/alacritty-hint-open`

### How Markdown URL Detection Works

The regex `https?://[^\s)'"<>\[\]]+` starts matching at `https://` and stops at whitespace or any of `)`, `'`, `"`, `<`, `>`, `]`, `[`. This naturally extracts just the URL from inside OpenCode's markdown syntax `[text](https://url)` — it skips the `[text](` prefix and stops before the closing `)`.

### Usage After Config

| Action | Result |
|--------|--------|
| Ctrl+Click on any detected link | Opens in browser |
| Ctrl+Shift+U | Enter hint mode — every URL gets a label key |
| Ctrl+Shift+U, type filter, press label key | Filter + open specific link |

Other terminal emulators (Kitty, WezTerm, iTerm2) have similar regex-based URL detection. The principle is the same: configure a URL-matching regex with an opener command.
