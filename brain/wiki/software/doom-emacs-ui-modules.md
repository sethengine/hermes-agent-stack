---
source_session: "20260704_175147_58c619"
category: software
date: "2026-07-04"
---

# Doom Emacs UI Modules

## Font/visual rendering modules (in `:ui` section of `init.el`)
| Module | Flag | Purpose |
|--------|------|---------|
| `ligatures` | — | Font ligatures (JetBrains Mono / Fira Code) |
| `emoji` | `+unicode` | Proper emoji font fallback |
| `indent-guides` | — | Indentation level visual guides |
| `zen` | — | Distraction-free writing with variable-pitch font centering |
| `smooth-scroll` | — | Smooth scrolling behavior |

## Beginner-friendly UI modules
| Module | Purpose |
|--------|---------|
| `treemacs` | File tree sidebar (togglable with `SPC t t`) |
| `tabs` | Tab bar at top |
| `shell` | `M-x shell` terminal inside Emacs |
| `editorconfig` | Auto-follow `.editorconfig` from projects |
| `nav-flash` | Flashes cursor line after big jumps |

## Editor modules
| Module | Purpose |
|--------|---------|
| `(format +onsave)` | Auto-format code on save via apheleia |
| `(spell +flyspell)` | Spell check with red underline |
| `snippets` | Yasnippet snippet engine (already on by default) |

## How to enable
1. Uncomment module in `~/.config/doom/init.el`
2. Run `doom sync`
3. Restart Emacs

## Related
- [[doom-emacs-bootstrap-fix]]
- [[emacs-font-rendering-wayland]]
- [[doom-emacs-ide-setup]]
