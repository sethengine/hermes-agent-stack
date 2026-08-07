---
source_session: 20260611_231513_ed3c26
date: 2026-06-11
category: software
tags: [chrome, performance, flags, memory, lightweighting, browser]
---

# Chrome Lightweighting via Flags and Settings

## Disable Internal Bloat Features
Add to `--disable-features` in `chrome-flags.conf` or command line:
```
ChromeWhatsNewUI,ChromeTipsInMainMenu,InterestFeedContentSuggestions,Translate,
ReadAnything,WebNotes,MediaRouter,MediaRemoting,PasswordImport,PasswordExport,
OptimizationHints,PrivacySandboxSettings4,SideSearch,HistoryClusters,QueryInOmnibox
```
Biggest RAM/CPU savers: `PrivacySandboxSettings4` (FLoC/Topics background JS), `Translate` (per-page language detection), `OptimizationHints` (background model downloads).

## Renderer Process Limits
- `--renderer-process-limit=8` — caps concurrent renderer processes
- `--max-uncached-process-count=8` — discards older processes

## Tab Discarding
```
--enable-features=ProactiveTabFreezeAndDiscard,TabDiscarding:discard_time_msecs/120000
```
Forces unused tabs out of memory after 2 min inactivity.

## Performance Settings
In `chrome://settings/performance`: enable **Memory Saver**, **Energy Saver**, set **Preload pages** to "No preloading" (biggest hidden bloat — Chrome prerenders entire pages speculatively).

## V8 Lightweighting
`--js-flags="--jitless --no-turbo --no-turbofan"` eliminates JIT compilation overhead (slower but less memory; best for static/document browsing).

[[chrome-js-blocking-techniques]] [[chrome-browser-troubleshooting]]
