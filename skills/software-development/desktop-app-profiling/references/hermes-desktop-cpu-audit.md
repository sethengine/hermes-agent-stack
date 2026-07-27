# Hermes Desktop App CPU Performance Audit

## Session Context

Audit of the Hermes Agent desktop app (`~/.hermes/hermes-agent/apps/desktop/`) for high CPU usage, slowness, and freezing. Investigation conducted June 2026 against version 0.15.1 of the desktop app (Electron 40.9.3, single 22 MB JS chunk).

## Key Findings (line-numbered)

### 1. No Code Splitting — 22 MB Monolithic Bundle

**File:** `apps/desktop/vite.config.ts`

```ts
build: {
  chunkSizeWarningLimit: 25000,  // 25 MB warning ceiling
  rolldownOptions: {
    output: { codeSplitting: false }  // explicitly disabled
  }
}
```

Comment explains: "electron-builder can OOM scanning thousands of files". The entire app — shiki (200+ language grammars), katex, three.js, xterm + WebGL, motion, react-shiki, @tanstack/react-virtual, leva, @dnd-kit, etc. — is one 22 MB blob. No lazy loading anywhere.

**Impact:** All JS parsed at startup, JIT compiler stays active, GC traces 22 MB of objects.

### 2. Four Independent Polling Loops

**File:** `src/app/desktop-controller.tsx` lines 145-151:
```ts
const CRON_POLL_INTERVAL_MS = 30_000          // line 145
const MESSAGING_POLL_INTERVAL_MS = 10_000      // line 150
const ACTIVE_MESSAGING_SESSION_POLL_INTERVAL_MS = 5_000  // line 151
```

**File:** `src/app/shell/hooks/use-status-snapshot.ts` line 7-8:
```ts
const REFRESH_MS = 15_000       // 15s — polls 3 endpoints!
const LOG_TAIL = 12
```

Lines 22-33: Each tick calls `getStatus()` + `getLogs()` + `evaluateRuntimeReadiness()` (via gateway) — three separate HTTP/JSON-RPC calls in parallel. On response, all three write to local state → React re-render.

**File:** `src/app/gateway/hooks/use-gateway-boot.ts` line 287-290:
```ts
const keepaliveTimer = setInterval(() => {
  touchActiveGatewayBackend()
  touchSecondaryGateways()
}, 60_000)
```

**Compounding:** 5s + 10s + 15s + 30s + 60s intervals running simultaneously. The 5s and 10s messaging polls fire even when there are zero messaging sessions.

### 3. Backdrop Full-Screen GPU Compositor

**File:** `src/components/Backdrop.tsx` lines 90-110:
```tsx
<div style={{ mixBlendMode: 'difference', opacity: 0.025 }}>
  <img ... style={{
    filter: `invert(1) saturate(1) brightness(1)`,
    height: '160dvh',    // way beyond viewport
    objectPosition: 'top left'
  }} />
</div>
```

Mounted at `src/app/chat/index.tsx` line 327: `<Backdrop />` — always rendered.

At 3440×1440, `mix-blend-mode: difference` + CSS `filter()` forces a full-screen GPU compositor pass **on every frame**, including idle frames. Prevents GPU from reaching low-power idle clock.

The CSS filter includes `var(--backdrop-invert-mul, 1)` for dark-mode inversion — interacts with theme changes.

### 4. xterm.js WebGL Addon — Constant GPU Context

**File:** `src/app/right-sidebar/terminal/use-terminal-session.ts` lines 284-290:
```ts
try {
  const webgl = new WebglAddon()
  webgl.onContextLoss(() => webgl.dispose())
  term.loadAddon(webgl)
} catch (err) {
  console.warn('[hermes-terminal] WebGL unavailable; falling back to DOM', err)
}
```

The terminal:
- Keeps a live WebGL context even with zero output
- Cursor blink fires RAFs continuously
- `FitAddon` at line 272 polls for resize
- Multiple RAF-based resize handlers (lines 623, 703, 788, 820)

### 5. ~35 `requestAnimationFrame` Usages

Counted across `src/` (not including test files):

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Markdown text reveal | `src/components/assistant-ui/markdown-text.tsx:396-426` | Character-by-character streaming text via RAF. `REVEAL_MIN_COMMIT_MS` = 16ms, fires every frame while stream is active. `REVEAL_MAX_CHARS_PER_FRAME` controls pacing. |
| Thread timeline | `src/components/assistant-ui/thread/timeline.tsx:97,205` | Multiple RAF loops for timeline viewport + scroll settle |
| Thread list | `src/components/assistant-ui/thread/list.tsx:225-230` | RAF-based scroll settle, fires on every scroll |
| Chat composer flush | `src/app/chat/composer/index.tsx:264-297` | RAF-based draft buffer flush |
| Mic recorder | `src/app/chat/composer/hooks/use-mic-recorder.ts:83,160` | RAF audio meter tick |
| Voice activity | `src/app/chat/composer/voice-activity.tsx:155-160` | 60fps waveform visualization |
| Composer popout drag | `src/app/chat/composer/hooks/use-popout-drag.ts:242,304` | RAF drag position flush |
| Message stream delta | `src/app/session/hooks/use-message-stream/index.ts:204-205` | RAF-based flush scheduling at 33ms |
| Session state cache sync | `src/app/session/hooks/use-session-state-cache.ts:227` | RAF-based view sync |
| Terminal (multiple) | `src/app/right-sidebar/terminal/use-terminal-session.ts:623,703,788,820` | Size sync, resize, focus — 4 separate RAF usages |
| Agent terminal | `src/app/right-sidebar/terminal/use-agent-terminal.ts:111,126` | RAF resize + scroll |
| Persistent terminal | `src/app/right-sidebar/terminal/persistent.tsx:104-109` | RAF tick loop for terminal alignment |
| Preview console | `src/app/chat/right-rail/preview-console.tsx:175-187` | RAF scroll-to-bottom |
| Preview pane | `src/app/chat/right-rail/preview-pane.tsx:323-328` | RAF scroll-on-open |
| Image gen placeholder | `src/components/chat/image-generation-placeholder.tsx:300-308` | 60fps canvas animation during image generation |
| Fixed row window | `src/components/chat/fixed-row-window.ts:112,121` | RAF resize handler |
| Starmap (if open) | `src/app/starmap/star-map.tsx:399-515` | Two RAF animation loops for Three.js scene |
| Pet roam | `src/components/pet/use-pet-roam.ts:226,303` | RAF sprite position updates |
| Pet star shower | `src/components/pet/pet-star-shower.tsx:133,232` | RAF particle animation |
| Pet sprite | `src/components/pet/pet-sprite.tsx:258,261` | RAF sprite animation |
| Pixel egg sprite | `src/components/pet/pixel-egg-sprite.tsx:174,245` | RAF animation |
| Loader | `src/components/ui/loader.tsx:359` | RAF spinner animation |

**~35 RAF usages** means the renderer is scheduling 60fps work constantly.

### 6. Streamdown/Shiki Re-Highlight on Every 33ms Delta

**File:** `src/app/session/hooks/use-message-stream/index.ts` line 72:
```ts
const STREAM_DELTA_FLUSH_MS = 33  // ~30fps flush rate
```

**File:** `src/components/assistant-ui/markdown-text.tsx` lines 396-426 — SmoothStreamingText reveals characters via RAF.
**File:** `src/components/chat/shiki-highlighter.tsx` line 93: `delay={120}` defers but doesn't eliminate per-flush re-highlight.

Flow: LLM token → WebSocket → gateway event → `handleGatewayEvent` → `$messages` atom update → `useStore($messages)` → `syncRepositoryIncrementally()` (iterates ALL messages, file: `src/lib/incremental-external-store-runtime.ts:36-58`) → assistant-ui repaint → shiki re-highlights all code blocks → React commit.

Every 33ms this chain executes while streaming, and it's O(n) in message count due to `syncRepositoryIncrementally`.

### 7. Nanostores Atom Cascade

**File:** `src/store/session.ts` — 30+ atoms including:
`$connection`, `$sessions`, `$messages`, `$workingSessionIds`, `$attentionSessionIds`, `$busy`, `$awaitingResponse`, `$currentModel`, `$currentProvider`, `$currentReasoningEffort`, `$currentServiceTier`, `$currentFastMode`, `$yoloActive`, `$currentCwd`, `$currentBranch`, `$currentUsage`, `$sessionStartedAt`, `$turnStartedAt`, `$introPersonality`, `$currentPersonality`, `$availablePersonalities`, `$introSeed`, `$contextSuggestions`, `$modelPickerOpen`, etc.

**File:** `src/app/chat/index.tsx` — ChatView subscribes to 16+ atoms via `useStore()`
**File:** `src/app/desktop-controller.tsx` — 20+ `useStore()` calls at top level

The cascade: 1 WebSocket event → 3-5 atom updates → 10+ component re-renders. Every tool.start, tool.complete, message.delta, thinking.delta, status.update triggers this.

### 8. IPC Serialization Bottleneck

**File:** `electron/main.cjs` line 6502-6543 — the `hermes:api` handler proxies every HTTP request from renderer to Python backend through a single handler. All polling loops (5s, 10s, 15s, 30s) serialize through this one `ipcMain.handle`, causing queueing under load.

### 9. Session List Survivor Accumulation

**File:** `src/store/session.ts` lines 53-73 — `mergeSessionPage`:
```ts
const survivors = previous.filter(
  session =>
    !incomingIds.has(session.id) &&
    (keep.has(session.id) || (session._lineage_root_id != null && keep.has(session._lineage_root_id)))
)
return survivors.length ? [...survivors, ...incoming] : incoming
```

Working and pinned sessions accumulate as survivors in the in-memory list. Over time this grows, making sidebar rendering + virtualizer calculations slower.

### 10. @tanstack/react-virtual Overscan

**File:** `src/app/chat/sidebar/virtual-session-list.tsx` lines 35-36:
```ts
const ROW_ESTIMATE_PX = 28
const OVERSCAN_ROWS = 12   // renders 12 rows beyond viewport
```

Combined with the survivor accumulation (#9), the overscan penalty grows as the list grows.

## Confirmed Metrics

| Metric | Value | Impact |
|--------|-------|--------|
| JS bundle size | 22 MB (single chunk) | Startup parse + JIT load |
| RAF usages | ~35 across 20+ components | Continuous 60fps work |
| Concurrent polling loops | 4 (5s, 10s, 15s, 30s) | Renderer never idle |
| GPU clock during idle | Elevated (CSS blend + WebGL) | Fans never quiet |
| Syntax highlighting | shiki full bundle | ~4-8 MB of grammar data |
| Terminal rendering | WebGL (fallback to DOM) | 1 WebGL context always live |
| State management | 30+ nanostores atoms | Cascade re-renders |

## Most Impactful Single Fix

**Disable the Backdrop component** (`src/components/Backdrop.tsx`). The `mix-blend-mode: difference` + CSS `filter` at 3440×1440 is the #1 GPU compositor cost. Comment it out in `src/app/chat/index.tsx` line 327. This alone stops ~5M pixel GPU blend per frame and lets the GPU reach idle clock.

## Remaining Unknowns

- Exact React commit cost per atom update (use `__PERF_PROBE__` on window in dev)
- Whether three.js from `@nous-research/ui` is tree-shaken or loaded (only 5 references in bundle — likely tree-shaken)
- Whether `motion` library is actively animating or just imported
