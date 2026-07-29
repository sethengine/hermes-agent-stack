# Electron App CPU/GPU Performance Audit

## When to Use

Use when a user reports "app uses too much CPU" or "fans spin up" for an Electron-based desktop app. Works for both the renderer process (Chromium) and the main process (Node.js).

## Architecture Primer

Electron apps have **two processes** — investigate both:

| Process | What it does | How to find CPU source |
|---------|-------------|----------------------|
| **Main** (Node.js) | Window management, IPC, child processes, native APIs | `top -p PID` — look for Node.js process |
| **Renderer** (Chromium) | React/Vue/Svelte UI, HTML/CSS rendering, WebGL, animations | Chrome DevTools (F12) → Performance tab |

## Investigation Checklist (in order)

### 1. Check Build Configuration

The single biggest perf factor: is code splitting enabled?

```typescript
// vite.config.ts — look for these anti-patterns:
build: {
  chunkSizeWarningLimit: 25000,  // > 500 tells you they expect big chunks
  rolldownOptions: {
    output: { codeSplitting: false }  // disabled = 20+ MB monolith
  }
}
```

- `codeSplitting: false` → all JS parsed at startup, higher idle CPU from JIT overhead
- Check `package.json` `dependencies` for bloated libs: shiki (full), three.js, katex, motion, gsap
- Check for tree-shakeable imports — unused Three.js/react-three-fiber still costs parse time

### 2. Find Polling Loops in the Renderer

```bash
# Search for periodic pollers
grep -rn 'setInterval\|const.*REFRESH\|const.*POLL\|const.*INTERVAL' src/ --include='*.ts' --include='*.tsx'
```

Common culprits:
- Status/health endpoint polling every 5-30s
- Log tail polling
- File watcher fallbacks (when OS-level inotify/FSEvents unavailable)

Each poll → HTTP request → JSON parse → state update → React re-render cascade.

### 3. Check for GPU-Composited CSS Effects

At high resolutions (4K, ultrawide 3440×1440), CSS blend modes and filters cost significantly more.

```bash
# Find GPU compositor-heavy CSS
grep -rn 'mix-blend-mode\|filter:\|backdrop-filter\|will-change' src/ --include='*.ts' --include='*.tsx' --include='*.css'
```

High-cost patterns:
- `mix-blend-mode: difference | screen | overlay` on full-window elements
- `filter: invert() saturate() brightness()` — forces per-frame GPU composite
- `backdrop-filter: blur()` at > 1080p
- Full-window `opacity` + `mix-blend-mode` layers
- Large background images with `filter` at high DP as fractional-opacity overlays

At 3440×1440 every full-screen CSS composite is ~5M pixels per pass.

### 4. Check for Continuous Render Loops

```bash
# Find WebGL contexts and animation loops
grep -rn 'WebGLRenderer\|WebglAddon\|requestAnimationFrame\|runRenderLoop\|useFrame' src/ --include='*.ts' --include='*.tsx'
```

Suspects:
- **xterm.js WebGL addon** — `new WebglAddon()` keeps a live WebGL context. Even idle, GPU clock stays elevated.
- **Three.js scenes** — check `@react-three/fiber` `useFrame`, manual `requestAnimationFrame`
- **CSS animations** (`@keyframes infinite`) — runs on compositor, but complex transforms cost at high DPR
- **ShaderMaterial with animated uniforms** — continuous upload per frame

Key question: is the render loop throttled? Check for:
- `runRenderLoop({ minIntervalMs: 100 })` (10fps) vs 33 (30fps) vs none (v-sync = whatever the display can push)
- GPU tier gating (`gpuTier === 1 ? 100 : 33`)

### 5. Check Terminal/Embedded Xterm

Embedded terminals are a common idle-time GPU drain:

```typescript
// High cost:
const webgl = new WebglAddon()
term.loadAddon(webgl)

// Lower cost (no WebGL context):
// Term.loadAddon(new DomAddon()) — or just omit the WebGL addon
```

WebGL addon maintains EGL/GLES context even with no output. Cursor blink + resize polling keeps the render loop warm.

### 6. Check Main Process for Background Tasks

```bash
grep -n 'setInterval\|watchFile\|fs.watch' electron/main.cjs
```

Things that run in the main process (Node.js, no GPU):
- 60s idle pool reapers
- File watchers (inotify on Linux)
- Cookie pollers during OAuth (only active during login, but look for 750ms intervals)
- Background update checkers
- Log flush timers

### 7. Check Dependency Tree for Bloat

```bash
# Find heavy dependencies
ls -lhS dist/assets/*.js | head -5
```

A 20+ MB JS bundle in a single chunk means the following are loaded at app start:
- **shiki** — full grammar bundle (all 200+ languages). Each code block is re-parsed on every React render.
- **three.js** — entire 3D engine, even if only used for a 2D noise shader
- **katex** — LaTeX rendering engine with full font set
- **motion / framer-motion / gsap** — full animation libraries
- **xterm** + addons — terminal emulator, WebGL renderer, Unicode support
- **leva** — debug GUI (often dev-only but bundled in prod)

## Performance Triage — by Symptom

### "High CPU when app is just sitting there (idle)"
→ #2 (polling loops), #3 (CSS composite), #4 (render loops), #5 (xterm WebGL)

### "High CPU only during streaming / tool calls"
→ #1 (monolithic bundle + shiki), #7 (re-highlighting on every token)

### "High CPU only on startup, then settles"
→ #1 (parse time for monolithic bundle). Normal for 22 MB single chunk.

### "GPU fans spin up, not CPU"
→ #3 (CSS blend modes), #4 (WebGL), #5 (xterm WebGL)

### "High CPU in main (Node.js) process"
→ #6 (background tasks, file watchers, pool reapers)

## Practical Mitigations (for reference)

These are common fixes users can apply — note them but let the user decide:

- **Disable backdrop/overlay effects**: comment out `<Backdrop />` or `<Noise />` in the component tree
- **Remove WebGL addon from xterm**: switch to DOM renderer
- **Increase poll interval**: `REFRESH_MS` from 15000 → 60000
- **Reduce virtual list overscan**: lower from 12 to 3-5
- **Enable code splitting** (if builds support it): split on routes/lazy-loaded routes
- **Use lighter syntax highlighter**: `highlight.js` tree-shaken vs shiki full
- **Check for `@nous-research/ui` overlays**: Noise, Glitch, Vignette overlays use Three.js shaders
