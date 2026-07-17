---
name: desktop-app-profiling
description: "Systematic performance investigation of desktop apps (Electron, Tauri, native) — identify polling loops, GPU compositor drain, render loops, IPC bottlenecks, bundle bloat, and state-management re-render cascades."
version: 1.0.0
author: Hermes Agent
created_by: agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, performance, profiling, electron, desktop, cpu, gpu]
    related_skills: [systematic-debugging, writing-plans]
---

# Desktop App Performance Profiling

## Overview

When a user reports that a desktop app "uses too much CPU", "is slow", "freezes", or "spins up the fans" — treat it as a **performance audit**, not a bug hunt. The goal is to find what's keeping the CPU and GPU busy **even when the app is idle**.

**Core principle:** Measure before you fix. Identify the specific subsystem consuming resources before proposing any change.

## Architecture Primer

Desktop apps have **multiple processes**. Target each one:

| Process | Technology | How to investigate |
|---------|-----------|-------------------|
| **Renderer** | Chromium (Electron) | Chrome DevTools (F12) → Performance, Console, Layers tabs |
| **Main** | Node.js (Electron) | `top`, `btop`, `ps aux`, `--inspect` profiler |
| **GPU** | Chromium GPU process | `nvidia-smi`, `radeontop`, Chrome `about:gpu` |
| **Utility** | Spawned subprocesses | `ps aux`, `btop` tree view |

## Investigation Checklist

### Phase 1: Baseline Telemetry

```bash
# Overall system
btop
# GPU state (NVIDIA)
nvidia-smi
nvidia-smi -q -d CLOCK   # idle clock should be ~210 MHz on modern RTX
# Process-level
ps aux | grep -E "electron|chrome|hermes" | grep -v grep
```

### Phase 2: Renderer Process Investigation

#### 2a. Check Build Configuration

The single biggest factor: is **code splitting** enabled?

```typescript
// vite.config.ts / webpack.config — anti-patterns:
build: {
  chunkSizeWarningLimit: 25000,     // >> 500 kB = expecting a monolith
  rolldownOptions: {
    output: { codeSplitting: false }  // disabled = 20+ MB single chunk
  }
}
```

- `codeSplitting: false` → all JS parsed at startup, JIT overhead persists
- Check `package.json` `dependencies` for heavy libs: shiki, three.js, katex, motion, gsap, xterm
- Check for tree-shaking gaps (unused imports that still ship)

#### 2b. Find Polling Loops

```bash
grep -rn 'setInterval\|const.*REFRESH\s*=\|const.*POLL\|const.*INTERVAL' src/ \
  --include='*.ts' --include='*.tsx' | grep -v node_modules | grep -v test
```

For EACH polling loop, note:
- Its interval (5s? 15s? 30s?)
- What it fetches (HTTP endpoint? file read?)
- What it triggers on completion (atom update? setState?)
- How the loops **compound** — multiple independent pollers at different intervals keep the renderer busy constantly

**Worst pattern:** Multiple polling loops with overlapping intervals (e.g. 5s + 10s + 15s), each triggering its own HTTP request → JSON parse → state update → React re-render cascade.

#### 2c. Check for GPU Compositor Effects

At high resolutions (4K, 3440×1440 ultrawide), CSS blend modes and filters cost significantly more:

```bash
grep -rn 'mix-blend-mode\|filter:\|backdrop-filter\|will-change' src/ \
  --include='*.ts' --include='*.tsx' --include='*.css' | grep -v node_modules
```

High-cost patterns (in order of severity):
1. Full-window `mix-blend-mode: difference` (forces per-frame GPU composite of every pixel)
2. Full-window `filter: invert() saturate() brightness()` + large images
3. `backdrop-filter: blur()` — expensive at high DPR
4. Multiple overlay layers stacked with blend modes
5. Large background images with CSS `opacity` + filters

**Why it matters:** At 3440×1440, every full-screen composite pass is ~5M pixels. Electron's Chromium compositor is aggressive — it composites every frame even when nothing changes.

#### 2d. Find Continuous Render Loops

```bash
grep -rn 'requestAnimationFrame\|cancelAnimationFrame\|WebGLRenderer\|WebglAddon\|useFrame\|runRenderLoop' src/ \
  --include='*.ts' --include='*.tsx' | grep -v node_modules | grep -v test | grep -v '.test.'
```

Count the occurrences. 30+ `requestAnimationFrame` usages across the app means **the renderer is doing work every 16ms** even at idle.

Key suspects:
- **xterm.js `WebglAddon`** — keeps a live WebGL context. GPU clock stays elevated even with zero terminal output.
- **Three.js shader animations** — continuous uniform uploads per frame
- **Text reveal animations** — character-by-character streaming text via RAF
- **Timeline/scroll animations** — thread timelines, scroll positioners
- **Voice/mic visualizations** — waveform rendering
- **CSS `@keyframes infinite`** — runs on compositor, but complex transforms still cost

For each RAF usage, check: is it **throttled**? (`minIntervalMs` > 16ms? GPU tier gating?)

#### 2e. Check State Management Re-render Cascade

```bash
grep -rn 'atom\|useStore\|subscribe\|nanostores\|recoil\|jotai\|zustand\|useSyncExternalStore' src/ \
  --include='*.ts' --include='*.tsx' | grep -v node_modules | grep -v '.test.'
```

Key questions:
- How many atoms/stores exist? (30+ is common in complex apps)
- How many `useStore()` / `subscribe()` calls exist in the component tree?
- Do WebSocket events update **multiple** atoms simultaneously?
- Are there heavy `useMemo` / `useCallback` computations in re-rendered components?

**The cascade pattern:** 1 WebSocket event → 3-5 atom updates → 10+ component re-renders. Every tool call, message delta, and status update from the backend triggers this chain.

#### 2f. Check Markdown/Syntax Highlighting Pipeline

When the app renders markdown or code blocks, check:
- Is syntax highlighting done on **every** re-render? (shiki, highlight.js, prism)
- Is the full language bundle loaded instead of a subset?
- Is highlighting triggered on **every** streaming token, or debounced?
- Are there character-by-character reveal animations on streamed text?

The common anti-pattern: streaming flushes at 30+ Hz → every flush triggers markdown re-parse → shiki re-highlights all code blocks → React re-renders the entire message tree.

#### 2g. Check Virtualized List Parameters

```bash
grep -rn 'useVirtualizer\|Virtualizer\|overscan\|OverScan' src/ \
  --include='*.ts' --include='*.tsx' | grep -v node_modules
```

- What's the `overscan` value? Values > 10 are aggressive.
- Does the list grow over time (accumulate survivors from multiple pages)?
- Is the estimate size accurate enough to avoid scroll jank?

### Phase 3: Main Process Investigation

#### 3a. Find Background Tasks

```bash
grep -n 'setInterval\|setTimeout.*loop\|watchFile\|fs.watch\|poll' electron/main.cjs
```

Common main-process background tasks:
- Backend pool idle reapers (e.g. 60s)
- File watchers (inotify/FSEvents)
- Cookie/session pollers during OAuth login
- Log flush timers
- Update checkers

#### 3b. Check IPC Handler Patterns

```bash
grep -n 'ipcMain.handle\|ipcMain.on' electron/main.cjs
```

Key questions:
- Is there a single generic IPC handler (e.g. `hermes:api`) that processes **all** HTTP requests? That's a serialization bottleneck.
- How large are the IPC payloads?
- Does the handler `await` backend requests serially?
- Are there any synchronous `ipcMain.on` handlers doing heavy work?

### Phase 4: GPU Process Investigation

#### 4a. Check Chrome GPU Internals

Visit `chrome://gpu` in the renderer to check:
- Is GPU rasterization enabled?
- Is WebGL working? (if not, fallback paths can be worse)
- Driver status (any software rendering fallbacks?)

#### 4b. Measure GPU Clock Under Load

```bash
nvidia-smi -q -d CLOCK   # Watch graphics clock
watch -n 2 nvidia-smi    # Watch utilization
```

If GPU clock stays above idle while the app is sitting on a static screen, something is forcing per-frame composites.

### Phase 5: Bundle Analysis

```bash
# Find the largest chunks
ls -lhS dist/assets/*.js | head -10

# Or for Vite builds
ls -lhS dist/*.js | head -10
```

A 20+ MB JS bundle means:
- Startup is slow (parse + compile time)
- JIT has more code to optimize
- GC has more objects to trace
- Every code path that gets exercised has higher cache pressure

Key libraries that bloat bundles:
| Library | Typical size | Why it's heavy |
|---------|-------------|----------------|
| shiki (full) | ~4-8 MB | 200+ language grammars + themes |
| three.js | ~1.2 MB | Full 3D engine |
| katex | ~500 KB + fonts | LaTeX engine + multiple font weights |
| motion/gsap | ~100-200 KB | Full animation engine |
| xterm + addons | ~700 KB | Terminal emulator + WebGL + Unicode |

## Performance Triage By Symptom

| Symptom | Most likely cause | Phase to check |
|---------|------------------|----------------|
| High CPU while app is idle | Polling loops + GPU compositor + render loops | 2b, 2c, 2d |
| High CPU only during streaming/tool calls | shiki re-highlight + markdown re-parse + atom cascade | 2f, 2e |
| High CPU on startup, settles | Monolithic bundle parse + JIT compile | 2a, 5 |
| GPU fans spin up, not CPU | CSS blend modes + WebGL + WebGL terminal | 2c, 2d |
| High CPU in Node.js process | Background tasks + IPC serialization | 3a, 3b |
| Freezes / stutters | Main thread blocking on IPC + heavy re-render | 3b, 2e, 2g |
| Memory grows over time | Survivor accumulation in virtual lists + polling state | 2g, 2b |

## Practical Mitigations

Present these to the user (don't apply without asking):

1. **Disable backdrop/overlay effects** — remove full-window CSS blend layers
2. **Increase poll intervals** — 15s → 60s for status, kill messaging polls if not used
3. **Disable WebGL terminal** — switch to DOM renderer (no WebGL context)
4. **Reduce virtual list overscan** — lower from 12 to 3-5
5. **Throttle RAF loops** — add `minIntervalMs` gating to non-critical animations
6. **Debounce syntax highlighting** — defer until streaming settles (already 120ms delay?)
7. **Enable code splitting** — split on routes/lazy-loaded views
8. **Use lighter highlighter** — tree-shaken highlight.js or prism vs shiki full
9. **Disable Three.js overlays** — remove Noise/Glitch/Vignette shader components

## References

- `references/hermes-desktop-cpu-audit.md` — Full session transcript and source-level findings from investigating the Hermes Agent desktop app (the app this skill was extracted from). Covers specific polling intervals, RAF usage counts, build config, and line-numbered references.
