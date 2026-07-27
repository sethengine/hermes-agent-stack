---
name: kde-plasma-theming
description: KDE Plasma 6 desktop theming — OCS API, KNewStuff framework, theme categories, bulk download patterns, rate-limit pitfalls, and CLI tools for theme management.
category: software-development
---

# KDE Plasma Theming

Tools, APIs, and workflows for managing KDE Plasma 6 themes — global themes, window decorations, color schemes, and plasma styles.

## Where Themes Live

### Official Sources

| Source | URL | Notes |
|--------|-----|-------|
| **KDE Store** | `https://store.kde.org` | Main community repo, JS-rendered React app |
| **Pling.com** | `https://pling.com` | Parent OpenDesktop ecosystem |
| **kde-look.org** | `https://kde-look.org` | Alias for visual content |
| **OpenDesktop API** | `https://api.kde-look.org/ocs/v1/` | OCS v1.6 API — no bot protection, returns JSON |

### Theme Category IDs (OCS API)

| cat_id | Name | Typical Count |
|--------|------|---------------|
| 722 | Global Themes (Plasma 6) | ~292 |
| 717 | Plasma 6 Window Decorations | ~216 |
| 112 | Plasma Color Schemes | ~2,168 |
| 104 | Plasma Themes / Styles (tagged Plasma 5) | ~888 |
| 114 | Aurorae Window Decorations | ~687 |

## OCS API Usage

Base URL: `https://api.kde-look.org/ocs/v1/content/data`

### Query parameters

| Param | Example | Notes |
|-------|---------|-------|
| `categories` | `722` | Category ID (see table above) |
| `format` | `json` | Returns JSON; omit for XML |
| `page` | `1` | 1-indexed pagination |
| `pagesize` | `100` | Max 100 per page |

### API call example

```
curl -sL "https://api.kde-look.org/ocs/v1/content/data?categories=722&format=json&page=1&pagesize=100"
```

Response fields of interest:
- `totalitems` / `itemsperpage` — pagination info
- `data[].id` — item ID (for KNS URLs)
- `data[].name` — human-readable name
- `data[].downloadlink1` — JWT-secured download URL
- `data[].downloadname1` — original filename
- `data[].downloadsize1` — size in KB
- `data[].downloadmd5sum1` — MD5 checksum (often stale; not reliable)

## Download Pipeline

The full chain from API to files on disk is a **3-phase process**:

| Phase | Action | Endpoint | Rate Limited? |
|-------|--------|----------|---------------|
| **1. Collect** | Fetch item metadata with `downloadlink1` (JWT URL) | `api.kde-look.org` OCS API | ❌ No |
| **2. Resolve** | Follow JWT URL's 302 redirect to get CDN URL | `files*.pling.com` | ✅ **Yes** |
| **3. Download** | Download file from CDN URL | `ocs-dl.*.digitaloceanspaces.com` | ❌ No |

### Phase 1: Collect Metadata (no rate limit)

```bash
curl -sL "https://api.kde-look.org/ocs/v1/content/data?categories=722&format=json&page=1&pagesize=100"
```

Returns items with fields: `id`, `name`, `downloadlink1` (JWT URL), `downloadname1`, `downloadsize1` (KB), `downloadmd5sum1` (often stale).

**Pagination:** OCS API may return empty `data` arrays for pages that exist per `totalitems` count. The API's count is a loose upper bound. Loop until `data` is empty.

```python
page = 1
all_items = []
while True:
    resp = api_get(f"...&page={page}&pagesize=100")
    items = resp.get("data", [])
    if not items: break
    all_items.extend(items)
    page += 1
    time.sleep(0.5)
```

### Phase 2: Resolve JWT → CDN URL (rate-limited)

**Critical: do NOT use `curl -sL` for the JWT URL — use a bodyless resolve to avoid consuming rate-limit bandwidth quota.**

```bash
# Get the CDN redirect URL without downloading anything
CDN_URL=$(curl -s -o /dev/null -w "%{redirect_url}" --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) KDE Plasma 6" \
  -H "Referer: https://store.kde.org/" \
  "$JWT_URL")
```

The JWT URL returns HTTP 302 with `Location` header pointing to:
```
https://ocs-dl.<region>.cdn.digitaloceanspaces.com/data/files/<id>/<filename>?X-Amz-Expires=3600&X-Amz-Signature=...
```

`X-Amz-Expires=3600` means the CDN URL is valid for **1 hour**.

### Phase 3: Download from CDN (no rate limit)

Once you have the CDN URL, download at full speed:

```bash
curl -sL -o theme.tar.xz --max-time 120 \
  -H "User-Agent: Mozilla/5.0" \
  "$CDN_URL"
```

DigitalOcean Spaces CDN does **not** rate-limit. Multiple downloads in rapid succession work at ~25MB/s per stream.

### PITFALL: Rate Limiting (the hard-learned part)

The `files*.pling.com` **JWT resolver** has aggressive per-IP rate limiting:

- **Symptoms:** HTTP 200 with XML body: `<?xml version="1.0"?><response><status>error</status><message>too many requests</message><retry_after>46</retry_after></response>`
- **Size:** ~147 bytes (small enough to fool size-only validation)
- **Retry after:** typically 40-60 seconds (value in XML)
- **Window:** ~20 requests per ~200-second sliding window

**Warning:** `curl -sL -o` following the full redirect chain hits the body-download path which exhausts the rate-limit budget faster. The resolve-only approach (`-o /dev/null -w "%{redirect_url}"`) uses less quota.

#### Two proven strategies:

**Strategy A — Slow steady (preferred for scripts):**
- **10-second gaps** between JWT URL resolves
- No explicit cooldown needed — stays within the 20/200s window naturally
- At 10s/item: ~10 hours for 3,751 items

**Strategy B — Burst + cooldown (faster per-burst):**
- Resolve ~12 JWT URLs with 2-second gaps (~24s)
- Wait 200s cooldown  
- Repeat
- At 12 items/224s: ~19 hours for 3,751 items

**Strategy A is simpler and recommended.** Both work; pick based on whether you want predictable pacing or bursty progress.

#### Detection and recovery:

```python
def is_rate_limit_error(filepath):
    """Check if downloaded content is a rate-limit XML error."""
    if not filepath.exists() or filepath.stat().st_size < 50:
        return False
    content = filepath.read_bytes()
    return b"too many requests" in content.lower() or b"retry_after" in content.lower()

def get_retry_after(filepath):
    """Extract retry_after from rate-limit XML."""
    import xml.etree.ElementTree as ET
    content = filepath.read_bytes()
    try:
        root = ET.fromstring(content)
        retry = root.findtext(".//retry_after", "0")
        return int(retry) if retry.isdigit() else 60
    except ET.ParseError:
        return 60
```

### Download caching / reuse

- JWT URLs collected in metadata survive ~1+ hour before the embedded token expires
- CDN URLs (extracted from 302) survive the full `X-Amz-Expires` duration (3600s)
- If a download fails mid-way, the CDN URL can be re-used for retries
- Stale JWT URLs produce HTTP 500 from the pling gateway (not 403/404)

## KNewStuff Framework (KNS)

### System .knsrc files

Located at `/usr/share/knsrcfiles/`:

| File | Purpose |
|------|---------|
| `lookandfeel.knsrc` | Global Themes (Plasma 6) |
| `window-decorations.knsrc` | Plasma 6 Window Decorations |
| `colorschemes.knsrc` | Color Schemes |
| `plasma-themes.knsrc` | Plasma Styles (tagged Plasma 5) |
| `aurorae.knsrc` | Aurorae Window Decorations |
| `kwineffect.knsrc` | KWin Effects |
| `kwinscripts.knsrc` | KWin Scripts |
| `ksplash.knsrc` | Splash Screens |
| `wallpaper.knsrc` | Wallpapers |

### Provider config

`https://autoconfig.kde.org/ocs/providers.xml` points to `api.kde-look.org/ocs/v1/` as the sole OCS provider.

### KNS URL format

```
kns://<knsrcfile>/<providerid>/<entryid>
```

Example: `kns://lookandfeel.knsrc/api.kde-look.org/2244767`

### CLI tool

```bash
# Opens a GUI dialog for browsing
knewstuff-dialog6 [knsrcfile]

# Show info for a specific item
knewstuff-dialog6 --url kns://lookandfeel.knsrc/api.kde-look.org/2244767
```

## CLI Theme Management Tools

| Command | Purpose |
|---------|---------|
| `kpackagetool6` | Install/uninstall KDE packages from local files |
| `plasma-apply-lookandfeel` | Apply a global theme |
| `plasma-apply-desktoptheme` | Apply a plasma style |
| `plasma-apply-colorscheme` | Apply a color scheme |
| `/usr/lib/plasma-apply-aurorae` | Apply Aurorae window decoration |
| `/usr/lib/kwin-applywindowdecoration` | Apply window decoration |

### kpackagetool6 usage

```bash
# Install a local package
kpackagetool6 --type Plasma/LookAndFeel --install theme.tar.xz

# List installed packages by type
kpackagetool6 --type Plasma/LookAndFeel --list
```

Available package types (from `kpackagetool6 --list-types`):
- `Plasma/LookAndFeel` — Global themes
- `Plasma/Theme` — Desktop themes/styles
- `Plasma/Applet` — Widgets
- `Plasma/Wallpaper` — Wallpaper plugins
- `KWin/Decoration` — KWin window decorations
- `KWin/Effect` — KWin effects
- `KWin/Script` — KWin scripts
- `KWin/Aurorae` — Aurorae themes

### Built-in installer (no CLI download needed)

```bash
# System Settings → Appearance → [category] → "Get New..."
```

This uses KNewStuff internally and handles all dependencies automatically. Safer and easier than manual downloads for individual themes.

## GitHub as a Theme Source

Many KDE Plasma 6 themes are developed on GitHub:

```
https://github.com/search?q=kde+plasma+6+theme&type=repositories&s=stars&o=desc
```

Top repos by stars (as of mid-2026):
- `juxtopposed/Mystical-Blue-Theme` — 1,174★ (full suite with Kvantum)
- `v1ewp0rt/BAREBLOOD` — 228★ (Gothic maximalist)
- `MathisP75/daemon-kde-mk2` — 147★ (full global theme)

## AUR Packages (Arch/Manjaro)

Search the AUR:
```bash
yay plasma6-theme
yay -Ss plasma6
```

## Script Usage

### Monolithic bulk downloader (`scripts/download-themes.py`)

Downloads all 5 categories in sequence. Suitable for overnight runs:

```bash
# All categories (default 10s gap — proven safe)
python3 scripts/download-themes.py

# Single category, custom delay, custom output
python3 scripts/download-themes.py --category 722 --delay 10 --dest ~/themes
```

The `--delay` default is **10 seconds**, which stays within the ~20-request-per-200s rate-limit window without needing explicit cooldowns. Values below 10s risk hitting the rate limit after 12-20 items and are not recommended for unattended runs.

### Per-category chunked downloader (`scripts/download-category.py`)

More reliable for interactive sessions — each category completes in 30-60 minutes, well under session timeouts:

```bash
# Run each category as its own background job with notification
python3 scripts/download-category.py 722 01-global-themes-p6 > cat_722.log 2>&1
# After completion notification:
python3 scripts/download-category.py 717 02-window-decorations-p6 > cat_717.log 2>&1
# etc.
```

See `references/background-process-reliability.md` for the platform timeout constraints that make per-category chunking the safer choice.

### Before restarting after an aborted run

Always clean up ~147-byte error XML files that may have been written as false positives:

```bash
find <archive-dir> -size -500c -type f -delete
```

The download scripts do this automatically at startup. If you're running manually, don't skip it — these small files will be treated as "already exists" on the next run and won't be re-downloaded.

## Lighter Aesthetic Themes (not pure white, not accessibility mode)

Users on KDE Plasma 6 often want lighter themes that are **NOT pure white** — warm off-whites, light grays, muted tones. This is distinct from accessibility "high contrast" modes (which use max-contrast black/white). These techniques target **aesthetic light themes with readable text contrast**.

### Recommended Themes

| Theme | Type | Why It Fits | Source |
|-------|------|-------------|--------|
| **Utterly Nord Light Solid** | Global Theme (P6) | Nord light palette (cool grays/soft blues - not white); "Solid" avoids transparency readability issues | KDE Store p/2151938 |
| **KDE Air (revived 6.7)** | Plasma Style | Soft light with blur effect; Oxygen-style dark glass also available; from KDE's own devs | Built into Plasma 6.7+ |
| **Slot-Plasma-Themes** | Theme Suite | 8+ color variants (lighter minimal to deep charcoal); unified GTK+Plasma; reduces KWin overhead ~15% | Bright Coding blog 2026/04 |
| **Klassy** | App Style + Global | Highly customizable decorations; Kvantum-based | github.com/paulmcauley/klassy |

### Frame Contrast (Plasma 6.6+) — frame border contrast, NOT text contrast

Customizable frame contrast was added to Plasma 6.6 (per akselmo.dev). **This setting affects window frame / border outline contrast, NOT text readability.** The slider controls how bold the outline is around frames, buttons, and panels — not how readable text is against its background.

**Location:** System Settings > Appearance > Application Style > Breeze > Fine Tuning
**Range:** 0 (no frame contrast) to 100 (maximum outline contrast)
**Scope:** QtQuick windows, QtWidgets/Breeze, Plasma SVG files

For **text** contrast (what matters for reading), see the Custom Color Scheme Editing section below.

### Custom Color Scheme Editing for Text Readability

Color scheme files are INI-format at `~/.local/share/color-schemes/`.

Key values for text contrast:
```
[Colors:View]
ForegroundNormal=49,54,59     # Dark text - change to lighter for high contrast
BackgroundNormal=255,255,255  # Default white bg
```

Technique: Create schemes with dark gray backgrounds and vibrant text colors rather than pure black-on-white. Adjust `ForegroundNormal` to ~144,144,144 for readability on both backgrounds (per r/kde).

### Desktop Icon Text Shadow / Outline

Plasma desktop icon labels (file/folder names on the desktop wallpaper) can have text shadows or outlines for readability:

| Value | Effect |
|-------|--------|
| 0 | No shadow (default) |
| 1 | Drop shadow |
| 2 | **Outline / contour** around characters |
| 3 | Both shadow and outline |

**GUI:** Right-click desktop > Configure Desktop > Icons > three-dot menu > Configure Folder View > Appearance > Text shadow dropdown

**CLI:**
```bash
kwriteconfig5 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
  --group Containments --group 2 --group General --key textShadow 2
```
Value is a positional argument -- no `--value` flag exists. `kwriteconfig5` syntax is `[options] value` where the value is the final positional arg.

### CLI Tools: kwriteconfig5 / kreadconfig5 Syntax

KDE's config CLI tools use positional value syntax, unlike many config tools:

```bash
# CORRECT -- value is last positional arg
kwriteconfig5 --file ~/.config/kwinrc --group Effect-MyEffect --key Enabled true
kreadconfig5 --file ~/.config/kwinrc --group General --key myKey

# WRONG -- will error: "Unknown option 'value'"
kwriteconfig5 --file x --group y --key z --value true  # --value doesn't exist
```

`kwriteconfig5` accepts `[options] value` per `--help`:
- `--group <g>` -- section header (repeatable for nested)
- `--key <k>` -- key name
- `--type <t>` -- `"bool"` for booleans, otherwise string
- `<value>` -- positional, mandatory (use `''` for empty)

### KWin Effects: Wayland vs X11

Not all KWin effects are available on Wayland. Key differences:

| Effect | X11 | Wayland (Plasma 6.6.x) |
|--------|-----|------------------------|
| Background Contrast (text readability behind panels) | ✅ Available in kwin-x11 | ❌ Plugin not loaded -- effect files under `/usr/share/kwin-x11/` only |
| Slide, Fade, Scale, Maximize | ✅ | ✅ |
| Cube | ✅ | ✅ (/usr/share/kwin/effects/ only has cube) |

The `Effect-BackgroundContrast` KWin config section (`~/.config/kwinrc`) can be written without error but is **silently ignored** on Wayland. There's no equivalent on Wayland in Plasma 6.6.x -- it may arrive in a later release.

To check available Wayland effects:
```bash
ls /usr/share/kwin/effects/          # User-installed Wayland effects
ls /usr/share/kwin/builtin-effects/  # Built-in Wayland effects
ls /usr/share/kwin-x11/effects/      # X11-only effects (contrast, fading popups, dimscreen, etc.)
```

### Plasma 6.7 Accessibility Improvements

- Grayscale color filter in accessibility settings
- Frame contrast slider became functional (was a no-op before 6.6)
- Air theme return with widget transparency + blur for legibility

### Research Note

When researching lighter KDE themes with `last30days`, the engine is thin on this specific topic (niche query). Supplement SearXNG web searches targeting:
- `KDE Plasma light theme not white high contrast`
- `KDE Plasma 6 Utterly Nord Light customization`
- `KDE Plasma color scheme edit ForegroundNormal`

See `references/lighter-high-contrast-themes.md` for the full research dump.

## Pitfalls

### Stale MD5 checksums
The `downloadmd5sum1` field in OCS API responses is often stale — the file on CDN may have been updated but the metadata still has the old checksum. Do NOT fail a download on MD5 mismatch; verify by size ratio (0.5x–3x of expected KB) instead.

### Empty page at the end
The OCS API may return an empty `data` array for pages that logically exist (e.g., `totalitems=292, pagesize=100 → page 3 should exist, but API returns 0 items`). Always break the pagination loop when `data` is empty, not when `page >= total_pages`.

### 147-byte error XML tricking size checks
Rate-limit XML responses are ~147 bytes. A naive `if file exists and size > 0` check will accept them as valid downloads. Always check for `> 500 bytes` minimum, or parse the content for `"too many requests"`.

### CDN URL reuse
CDN URLs from DigitalOcean Spaces (with `X-Amz-Expires=3600`) are reusable for retries within the 1-hour window. If a CDN download fails mid-stream, retry the same CDN URL rather than re-resolving the JWT.

### Variable scoping in downloader scripts

When a `resolve_and_dl()` function returns `"exists"`, the caller needs the file path to count size. Either return the path alongside the status, or compute size from the filename. The `scripts/download-themes.py` reference handles this by counting existed files rather than summing sizes at the call site.

### Background processes killed by session lifecycle (SIGTERM 143)

Background processes with `notify_on_complete=true` may be killed after ~8 minutes (exit code 143 / SIGTERM). **This is caused by the notification delivery lifecycle reaping the child process, not a general session timeout.**

**Fix:** Omit `notify_on_complete=true` from `terminal(background=true, ...)`. Processes launched without it survive indefinitely — tested at 33+ minutes without issue. Poll manually with `process(action='poll')` and read stdout via `process(action='log')` or a redirected log file.

**Log staleness:** Even with `python3 -u`, shell `>` redirect can buffer output for minutes due to OS pipe buffer (4KB default). When monitoring a running process that has stopped producing log lines, use `process(action='poll')` to check if the process is alive or dead before assuming it stalled. Prefer `stdbuf -oL python3 -u` over plain `python3 -u` for shell-redirected output.

See `references/background-process-reliability.md` for full details.

## References

- `references/rate-limit-patterns.md` — Detailed rate-limit profile, tested gap values, cooldown behavior, and URL lifetime data
- `references/background-process-reliability.md` — SIGTERM patterns, log buffering, and per-category chunking strategy
- `references/ocs-api-detail.md` — Example API responses and pagination edge cases
- `references/lighter-high-contrast-themes.md` — Lighter KDE themes with high-contrast text (not pure white): theme catalog, frame contrast, custom color scheme editing, and research queries
- `scripts/download-themes.py` — Full multi-category bulk downloader (v4 pipeline)
- `scripts/download-category.py` — Per-category downloader for reliable chunked execution
