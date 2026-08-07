---
source: "20260607_133607_d74665"
date: "2026-06-07"
category: "software"
---

# Hermes Desktop App Performance Analysis

Deep analysis of CPU/GPU/memory issues in the Hermes Electron desktop app.

## Critical Issues

### 1. 22 MB Monolithic JS Bundle (No Code Splitting)
`vite.config.ts` disables code splitting (`codeSplitting: false`) because electron-builder OOMs on thousands of chunks. All deps (shiki, three.js, xterm, katex, motion, etc.) parsed at startup.

### 2. Four Independent Polling Loops
| Loop | Interval |
|------|----------|
| Status snapshot | 15s — 3 HTTP endpoints |
| Messaging sessions | 10s |
| Active messaging session | **5s** (worst offender) |
| Cron job sessions | 30s |
Each triggers HTTP → JSON parse → nanostores atom updates → React re-renders.

### 3. Backdrop GPU Compositor (Always Mounted)
At `src/components/Backdrop.tsx` — full-screen `mix-blend-mode: difference` + CSS filters (`invert`, `saturate`). At 3440×1440 this prevents GPU from idling.

### 4. xterm.js WebGL Addon
`src/app/right-sidebar/terminal/use-terminal-session.ts:284-290` — WebGL canvas context stays active even when terminal is idle, keeping GPU clock elevated.

### 5. ~35 requestAnimationFrame Calls
Markdown text reveal, thread timeline, terminal fit, composer draft flush, starmap, voice activity — multiple concurrent 60fps loops.

### 6. shiki Full-Bundle Re-Highlight Every 33ms
Streaming flushes every 33ms (`STREAM_DELTA_FLUSH_MS`), re-highlighting all code blocks with 200+ language grammars loaded.

## Quick Fixes (Highest Impact)

1. **Kill Backdrop** — comment out `<Backdrop />` in `src/app/chat/index.tsx`
2. **Slow polling** — change 5s/10s to 30s/120s
3. **Remove terminal WebGL** — delete `WebglAddon` load in terminal hook
4. **Disable smooth reveal** — skip `useSmoothReveal` RAF loop in markdown-text.tsx
5. **Reduce stream flush** — change `33` to `100` ms
6. **`HERMES_DESKTOP_DISABLE_GPU=1`** — forces CPU rendering, lets GPU idle

## Related
- [[nvidia-dmar-fault-crash-cascade]] (same system, GPU load context)
