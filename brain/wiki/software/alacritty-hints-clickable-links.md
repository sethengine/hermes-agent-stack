---
tags: [alacritty, hints, links, clickable, osc-8, terminal, opencode, url-detection]
source_session: 20260601_153108_8d25f4
category: software
wiki-links: [alacritty_config_best_practices, opencode_research_agent_setup]
---

# Alacritty Hints: Making Terminal Links Clickable

Alacritty supports **hints** — regex-based URL detection that makes underlined text actually clickable. Without hints configured, links displayed with ANSI color/underline styling (as OpenCode renders them) are visually highlighted but not actionable.

## Architecture

Two mechanisms for terminal links:

| Mechanism | What it does | OpenCode support |
|-----------|-------------|-----------------|
| **ANSI styling** (SGR) | Underline + color to look like a link | Yes — but not clickable |
| **OSC 8 sequences** (`\e]8;;URL\e\\...\e]8;;\e\\`) | Makes text actually clickable | No — OpenCode doesn't emit these |

Since OpenCode uses only ANSI styling, Alacritty hints bridge the gap with regex detection.

## Configuration (`~/.config/alacritty/alacritty.toml`)

### Ctrl+Click on URLs

```toml
[mouse]
hide_when_typing = true
```

In Alacritty 0.17+, mouse URL config is done through hint definitions (not a top-level `url` key). The legacy `url = { modifiers = "Control" }` under `[mouse]` was deprecated and produces an `Unused config key` warning.

### Hint Definitions

```toml
[hints.enabled]
# Plain URLs (https://... and www...)
regex = "https?://[^\\s)'\"<>\\[\\]]+"
command = { program = "xdg-open", args = [] }
mouse = { enabled = true, modifiers = "Control" }
binding = { key = "U", mods = "Control|Shift" }

# Markdown links — extracts URL from ](URL) pattern
regex = "\\]\\(([^)]+)\\)"
command = { program = "bash", args = ["-c", "xdg-open ${1}"] }
mouse = { enabled = true, modifiers = "Control" }
binding = { key = "U", mods = "Control|Shift" }

# GitHub refs — owner/repo#123
regex = "[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+#[0-9]+"
command = { program = "bash", args = ["-c", "xdg-open https://github.com/${0}"] }
mouse = { enabled = true, modifiers = "Control" }
binding = { key = "U", mods = "Control|Shift" }
```

## Alacritty Regex Limitations

- **No `\b` word boundaries** — Alacritty's regex DFA engine does not support `\b`. Patterns must use explicit character classes instead.
- **Only `Copy`, `Paste`, `Select`, `MoveViModeCursor`** are valid `action` values. There is no `action = "Open"`. Use `command = { program = "...", args = [...] }` instead.
- The `command` field passes matched text as arguments to the program.

## Clickable Link Wrapper Script

For handling non-URL patterns (GitHub refs, arXiv IDs) that `xdg-open` cannot process directly, a wrapper script at `~/.local/bin/alacritty-hint-open` maps:

| Matched pattern | Expanded URL |
|----------------|-------------|
| `https://...` | (as-is) |
| `owner/repo#123` | `https://github.com/owner/repo/issues/123` |
| `YYYY.NNNNN` | `https://arxiv.org/abs/YYYY.NNNNN` |

## Usage

| Action | Result |
|--------|--------|
| **Ctrl+Click** on URL | Opens in browser immediately |
| **Ctrl+Shift+U** | Enters hint mode — every detected URL gets a label |
| **Ctrl+Shift+U, type filter, press key** | Filter and open specific URL |

## Key Detail

The single URL regex `https?://[^\s)'"<>\[\]]+` handles both plain URLs and URLs embedded in markdown `[text](https://url)` syntax because it starts matching at `https://` and stops before `)`, `]`, or whitespace — naturally extracting the URL from inside markdown parentheses.
