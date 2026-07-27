---
name: hermes-dashboard-theming
description: "Create, apply, and troubleshoot custom dashboard themes for Hermes Desktop — YAML-based palette, typography (fonts), layout, and component overrides."
version: 1.1.0
author: agent
license: MIT
---

# Hermes Dashboard Theming

The Hermes Agent has **two separate web frontends** — people mean different
things by "the dashboard" depending on which one they're looking at:

| Frontend | Source | Build output | How to run |
|----------|--------|-------------|------------|
| **CLI dashboard** | `web/src/` | `hermes_cli/web_dist/` | `hermes dashboard` (served by FastAPI) |
| **Electron desktop app** | `apps/desktop/` | `apps/desktop/dist/` | Installed desktop application (released builds) |

This skill covers **both** — but the mechanism for customizing each is different.

### Key Architectural Insight

The **Electron desktop app** already ships with Apple SF fonts baked in.
The source code at `apps/desktop/` configures SF Pro Text, SF Pro Display,
and SF Mono as the default font stacks for both the UI and the embedded
terminal. If the user is asking about the desktop app's fonts, the answer
is "it already uses them" — changes to `web/src/` won't affect the desktop
app, and vice versa.

### Theme system (shared concept)

Both frontends support user-created themes via YAML files in
`~/.hermes/dashboard-themes/`. Themes override palette, typography
(font families, sizes, line-height), layout (radius, density), assets,
component styles, and raw CSS — all without forking the codebase.

**When to use this skill:**
- Changing dashboard fonts (sans-serif, monospace, display)
- Creating a custom color palette for the dashboard
- Adjusting layout density or corner radius
- Adding background images or per-component chrome
- Diagnosing why a theme change didn't take effect

**Official docs:** `website/docs/user-guide/features/extending-the-dashboard.md`
(in the Hermes Agent source tree).

---

## Theme System Architecture

```
~/.hermes/dashboard-themes/<name>.yaml   ← drop-in, no rebuild
       │
       ▼
hermes_cli/web_server.py                ← _discover_user_themes() scans dir
       │
       ▼
GET /api/dashboard/themes               ← returns built-ins + user themes
       │
       ▼
web/src/themes/context.tsx              ← ThemeProvider calls applyTheme()
       │
       ▼
:root CSS vars set via setProperty()     ← --theme-font-sans, --theme-font-mono, ...
       │
       ▼
index.css + Tailwind consume vars        ← font-family: var(--theme-font-sans)
```

**Key insight:** ThemeProvider writes CSS vars via `root.style.setProperty()`,
which beats `:root {}` specificity. So user themes ALWAYS win over the
built-in defaults.

### Two separate font contexts

Each frontend has its own font configuration — they don't share source files:

#### CLI dashboard (`web/src/`)

| Context | Driven by | How to change |
|---------|-----------|---------------|
| Dashboard UI (pages, chrome) | Theme `typography` block | YAML theme — no rebuild |
| Embedded terminal (Chat tab) | Hardcoded in `ChatPage.tsx` | Source patch + `npm run build` in `web/` |

#### Electron desktop app (`apps/desktop/`)

| Context | Driven by | How to change |
|---------|-----------|---------------|
| Dashboard UI | CSS vars in `styles.css` + `themes/presets.ts` | Already defaults to SF fonts — patch source + `npm run build` in `apps/desktop/` |
| Embedded terminal | Hardcoded in `use-terminal-session.ts` | Already defaults to SF Mono — patch source + rebuild |

The terminal's `fontFamily` is passed directly to the xterm.js `Terminal`
constructor — it does NOT read CSS variables. This is a known limitation;
the theme system only provides `terminalBackground` for the terminal,
not a font.

---

## Quick Start — Theme YAML

**Template available:** `templates/sf-fonts-theme.yaml` — a working example
using locally-installed Apple SF Pro + SF Mono fonts (copy to
`~/.hermes/dashboard-themes/` and customize).

```bash
mkdir -p ~/.hermes/dashboard-themes
```

Minimal theme (two colors):
```yaml
# ~/.hermes/dashboard-themes/my-theme.yaml
name: my-theme
label: My Theme
description: A custom theme

palette:
  background: "#0a0a1f"
  midground: "#d4c8ff"
```

Full theme with typography (local fonts, no external stylesheet):
```yaml
name: my-theme
label: My Theme
description: Custom palette + fonts

palette:
  background:
    hex: "#0a0a1f"
    alpha: 1.0
  midground:
    hex: "#d4c8ff"
    alpha: 1.0
  foreground:
    hex: "#ffffff"
    alpha: 0.0
  warmGlow: "rgba(167, 139, 250, 0.32)"
  noiseOpacity: 0.8

typography:
  fontSans: '"Inter", system-ui, -apple-system, sans-serif'
  fontMono: '"JetBrains Mono", ui-monospace, monospace'
  fontDisplay: '"Inter", system-ui, sans-serif'
  baseSize: "15px"
  lineHeight: "1.55"
  letterSpacing: "0"

layout:
  radius: "0.5rem"
  density: comfortable
```

### Typography fields

| Field | CSS maps to | Notes |
|-------|-------------|-------|
| `fontSans` | `--theme-font-sans` → `html, body` | Body copy stack |
| `fontMono` | `--theme-font-mono` → `code, pre, .font-mono` | Code/terminal chrome |
| `fontDisplay` | `--theme-font-display` | Optional heading stack, falls back to `fontSans` |
| `fontUrl` | Injected as `<link rel="stylesheet">` | For Google/Bunny Fonts. **Omit** when fonts are installed locally (system fonts). |
| `baseSize` | `--theme-base-size` → `html { font-size }` | Controls rem scale |
| `lineHeight` | `--theme-line-height` | Body line-height |
| `letterSpacing` | `--theme-letter-spacing` | Body letter-spacing |

### Using locally-installed fonts

When fonts are installed system-wide (e.g., `/usr/share/fonts/` on Linux,
`/Library/Fonts/` on macOS), **do NOT set `fontUrl`**. Just use the font
family name in the CSS stack:

```yaml
typography:
  fontSans: '"SF Pro Text", "SF Pro", system-ui, sans-serif'
  fontMono: '"SF Mono", ui-monospace, monospace'
  # NO fontUrl — fonts come from the OS, not the web
```

Verify local font names with `fc-list | grep -i "<family>"` on Linux
or Font Book on macOS.

**Desktop app note:** The Electron desktop app (`apps/desktop/`) already
defaults to SF Pro Text + SF Mono. If the user is running the desktop
app and asking about SF fonts, the fonts are already configured — no
changes needed. If they're running `hermes dashboard` (CLI dashboard),
they need a YAML theme or source patches to use SF fonts.

### Activating a theme

```bash
# Set as active
hermes config set dashboard.theme my-theme

# Or switch live from the dashboard: click palette icon in header bar
```

The selection persists in `config.yaml` under `dashboard.theme` and is
restored on reload.

---

## Changing the Terminal Font

**CLI dashboard** (`web/src/`): The embedded xterm.js terminal (Chat tab)
has a **hardcoded** `fontFamily` in `web/src/pages/ChatPage.tsx` (line ~302).
It's NOT driven by the theme system.

To change it for the CLI dashboard:

1. **Patch the source:**
   ```
   web/src/pages/ChatPage.tsx — fontFamily in Terminal constructor
   ```

2. **Rebuild the web app:**
   ```bash
   cd ~/.hermes/hermes-agent/web && npm run build
   ```
   Output goes to `hermes_cli/web_dist/` (NOT `web/dist/`).

3. **Restart the dashboard:**
   ```bash
   # Stop existing, then:
   hermes dashboard --skip-build
   ```

**Electron desktop app** (`apps/desktop/`): The terminal font is hardcoded
in `apps/desktop/src/app/right-sidebar/terminal/use-terminal-session.ts`
(line ~264). It already defaults to `"'SF Mono', 'Menlo', 'Cascadia Code', 'JetBrains Mono', monospace"`.
To change it, patch that file then rebuild:

```bash
cd ~/.hermes/hermes-agent/apps/desktop && npm run build
```

### Also update these CSS/TS defaults (optional, for new profiles)

- `web/src/index.css` — `:root` CSS vars (`--theme-font-sans`, `--theme-font-mono`)
  These are the initial values before ThemeProvider loads.
- `web/src/themes/presets.ts` — `SYSTEM_SANS` / `SYSTEM_MONO` constants
  These feed `DEFAULT_TYPOGRAPHY` which is the base for all built-in themes.

---

## Pitfalls

- **Wrong frontend trap.** Hermes has TWO separate frontends (`web/src/`
  for CLI dashboard, `apps/desktop/` for the Electron app). Always confirm
  which one the user is asking about before making changes. Patching the
  wrong one wastes time and confuses everyone.

- **Terminal font ignores theme typography.** The `typography.fontMono`
  field controls dashboard UI code blocks, NOT the embedded terminal.
  The terminal requires a separate source patch in `ChatPage.tsx` (CLI)
  or `use-terminal-session.ts` (desktop).

- **`fontUrl` only for web fonts.** If fonts are installed locally,
  omit `fontUrl` entirely. Including it loads an unnecessary external
  stylesheet.

- **Build output goes to `hermes_cli/web_dist/`, not `web/dist/`.**
  The `web/dist/` directory is for the Tauri desktop app installer.
  The dashboard web server reads from `hermes_cli/web_dist/`.

- **Restart required after source patches.** User themes load at runtime
  (no restart), but source patches to `.tsx`/`.css`/`.ts` files need a
  rebuild + dashboard restart.

- **YAML indentation matters.** Use 2-space indentation. The backend
  parses with Python's `yaml.safe_load()`. Invalid YAML silently falls
  back to the default theme — check `~/.hermes/logs/errors.log`.

- **Font family names must match exactly.** On Linux, use `fc-list` to
  verify the exact family name (e.g., "SF Pro Text" not "SF ProText").
  CSS `font-family` matches against the PostScript family name.

---

## Verifying Theme Loads

```bash
# Check API response includes your theme
curl -s http://127.0.0.1:9119/api/dashboard/themes | python3 -m json.tool | grep -A3 '"name": "my-theme"'

# Check active theme in config
grep 'theme:' ~/.hermes/config.yaml

# Check for YAML parse errors
grep -i 'theme' ~/.hermes/logs/errors.log | tail -10
```

---

**Reference file:** `references/apple-sf-font-configuration.md` — complete
reference for Apple SF font names, weights, verification commands, and
exact file paths in both frontends.
