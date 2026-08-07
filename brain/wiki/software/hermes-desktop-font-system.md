---
source_session: "20260604_193132_471451"
category: software
tags: [hermes, desktop, fonts, sf-pro, theming, electron]
---

# Hermes Desktop Font System

Hermes Desktop (Electron app at `apps/desktop/`) uses CSS custom properties for fonts — no built-in UI setting exists to change them.

## Font Stack Architecture

| Property | Default Preference | Scope |
|----------|-------------------|-------|
| `--dt-font-sans` | `SF Pro Text`, `SF Pro Display`, `Segoe WPC`, ... | Dashboard UI |
| `--dt-font-mono` | `SF Mono`, `Cascadia Code`, `JetBrains Mono`, ... | Code blocks, terminal |

The embedded terminal (xterm.js) has a **hardcoded** `fontFamily` in `ChatPage.tsx` — not theme-driven. Requires source patch + rebuild.

## Theme Override System

User themes in `~/.hermes/dashboard-themes/*.yaml` override `typography.sans` / `typography.mono` at runtime via `ThemeProvider` → CSS vars on `:root`. No rebuild needed for dashboard-level fonts.

To change terminal font, patch `web/src/pages/ChatPage.tsx` → `xtermOptions.fontFamily`, then rebuild:

```bash
cd ~/.hermes/hermes-agent && npm run build
```

## Pre-installed SF Fonts

Apple SF families at `/usr/share/fonts/apple-fonts/`: SF Pro, SF Pro Display, SF Pro Text, SF Mono, SF Compact, New York. Built CSS already references them first in the stack.

To switch from Courier Prime (Nous theme), override in `presets.ts` → `nous.typography.mono`.

Related: [[hermes-ansi-terminal-coloring]], [[hermes-mcp-server-troubleshooting]], [[hermes-desktop-app-cpu-optimizations]]
