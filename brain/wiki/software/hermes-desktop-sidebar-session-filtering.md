---
source_session: 20260730_212424_4b7e0f
date: 2026-07-30
category: software
tags: [hermes, desktop, sidebar, sessions, filtering, cron, ui]
related: [hermes-desktop-font-system, hermes-desktop-gpu-flags-config]
---

# Hermes Desktop Sidebar Session Filtering

The sidebar applies two filtering layers before showing sessions:

**Layer 1 — Source split.** Sessions are divided into three sections: **Recents** (sources `cli`, `tui`, `desktop`, `codex`, `gateway`, `local`), **Cron Jobs** (`cron` only), and **Messaging** (chat apps). Cron sessions are deliberately separated so cron bursts don't bury conversations. Code at `apps/desktop/src/lib/session-source.ts:45`.

**Layer 2 — Page size limit.** Each section loads 50 sessions at a time (`SIDEBAR_SESSIONS_PAGE_SIZE=50` in `apps/desktop/src/store/layout.ts:20`). Clicking "Load more" calls `bumpSessionsLimit()` to add 50 and re-fetch.

Additionally, `min_messages=1` in the sidebar query drops zero-message sessions.

**To see all sessions at once:** `Cmd+K` opens the session picker (fetches 200 from all sources) or `hermes sessions list --limit 200` from CLI.
