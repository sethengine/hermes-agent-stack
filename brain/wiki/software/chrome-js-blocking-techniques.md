---
source_session: 20260611_231513_ed3c26
date: 2026-06-11
category: software
tags: [chrome, javascript, ublock-origin, noscript, performance, privacy]
---

# Preventive JavaScript Blocking in Chrome

## uBlock Origin (Best General Tool)
- **Medium mode**: blocks all 3rd-party scripts/frames by default, allowlist per-site
- **Hard mode**: blocks all scripts globally, unblock per-site
- Dynamic filtering allows JS only from specific origins

## Chrome Built-in JS Blocking
`chrome://settings/content/javascript` — set "Don't allow sites to use JavaScript" with per-site exceptions (nuclear option, breaks many sites).

## Chrome Flags
- `#enable-third-party-keyboard-blocking` — blocks JS intercepting keyboard events on 3rd-party frames (privacy + perf)
- `#enable-lazy-frames-loading` — defers offscreen iframes (often already on)
- `--disable-javascript` command-line flag — disables V8 entirely; useful for a separate profile reading static content

## Extension Alternatives
- **NoScript** — fine-grained per-domain JS control
- **uMatrix** (unmaintained) — uBlock Origin's dynamic filtering supersedes it

## Profile Strategy
Run a second Chrome profile with `--disable-javascript` for docs/news without JS overhead, keep main profile normal for JS-heavy sites.

[[chrome-lightweighting-flags]] [[chrome-browser-troubleshooting]]
