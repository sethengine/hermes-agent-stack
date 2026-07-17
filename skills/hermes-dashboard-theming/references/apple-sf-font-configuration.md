# Apple SF Font Configuration Reference

Font paths, verification commands, and source file locations for SF fonts
in both Hermes frontends (CLI dashboard + Electron desktop app).

## Installed Font Locations

```
/usr/share/fonts/apple-fonts/  — Linux (Arch/Manjaro via apple-fonts package)
/Library/Fonts/                — macOS (installed natively)
```

## Verification Commands

```bash
# Check if fonts are installed
fc-list | grep -i "SF Pro\|SF Mono\|New York"

# Verify exact family names (CSS must match exactly)
fc-match "SF Pro Text"      # → SF-Pro-Text-Regular.otf
fc-match "SF Pro Display"   # → SF-Pro-Display-Regular.otf
fc-match "SF Mono"          # → SF-Mono-Regular.otf
fc-match "SF Pro"           # → SF-Pro.ttf

# List all available weights
fc-list ":family=SF Mono" file
fc-list ":family=SF Pro Text" file
fc-list ":family=SF Pro Display" file
```

## Font Family Names (for CSS font-family)

| CSS name | Available weights | Used for |
|----------|------------------|----------|
| `"SF Pro Text"` | Thin → Black + Italics | Body text (≤19pt) |
| `"SF Pro Display"` | Thin → Black + Italics | Headings/larger text |
| `"SF Pro"` | Regular, Black, Heavy, Expanded variants | Fallback (variable font TTF) |
| `"SF Mono"` | Light → Heavy + Italics (Bold ✓) | Monospace/code/terminal |
| `"SF Compact"` | Display, Text, Rounded variants | Alternate compact face |
| `"New York"` | Small, Medium, Large, ExtraLarge | Serif alternative |

## CLI Dashboard Font Files (`web/src/`)

| File | What it sets |
|------|-------------|
| `web/src/index.css` | `:root` CSS vars (`--theme-font-sans`, `--theme-font-mono`) — initial defaults before ThemeProvider |
| `web/src/themes/presets.ts` | `SYSTEM_SANS` / `SYSTEM_MONO` constants — feed `DEFAULT_TYPOGRAPHY` for all built-in themes |
| `web/src/themes/context.tsx` | `applyTheme()` — writes CSS vars via `root.style.setProperty()` on theme switch |
| `web/src/pages/ChatPage.tsx` (line ~302) | Terminal `fontFamily` — hardcoded in xterm.js `Terminal` constructor |

**Build:** `cd web && npm run build` → outputs to `hermes_cli/web_dist/`

## Electron Desktop App Font Files (`apps/desktop/`)

| File | What it sets |
|------|-------------|
| `apps/desktop/src/styles.css` (line ~265) | `--dt-font-sans`, `--dt-font-mono` CSS vars — defaults for the entire app |
| `apps/desktop/src/themes/presets.ts` | `SYSTEM_SANS` / `SYSTEM_MONO` — feed theme typography constants |
| `apps/desktop/src/app/right-sidebar/terminal/use-terminal-session.ts` (line ~264) | Terminal `fontFamily` — hardcoded |
| `apps/desktop/src/components/chat/image-generation-placeholder.tsx` (line ~132) | Canvas font for image generation placeholder text |

**Already uses SF fonts by default** in all the above files.
**Build:** `cd apps/desktop && npm run build` → outputs to `apps/desktop/dist/`

## User Theme YAML

For the CLI dashboard, create `~/.hermes/dashboard-themes/<name>.yaml`:

```yaml
typography:
  fontSans: '"SF Pro Text", "SF Pro Display", "SF Pro", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
  fontMono: '"SF Mono", ui-monospace, "Cascadia Mono", Menlo, Consolas, monospace'
  fontDisplay: '"SF Pro Display", "SF Pro Text", "SF Pro", system-ui, -apple-system, sans-serif'
  # NO fontUrl — these are local fonts, not web fonts
```

Activate with `hermes config set dashboard.theme <name>`.
