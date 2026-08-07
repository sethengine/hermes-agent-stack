---
title: Hermes Desktop App Slash Command Autocomplete
category: software
tags: [hermes, desktop, tui, autocomplete, slash-commands, frontend]
source_session: 20260725_205740_30c7a7
created: 2026-07-29
related: [[hermes-shell-completion]], [[hermes-desktop-build]]
---

# Hermes Desktop App Slash Command Autocomplete

Investigation of broken slash command autocomplete in the Hermes desktop app (TUI). The user reported that `/`-command popover completion was not working correctly.

## Root Cause

Commit `f7c9feb39` ("fix(desktop): only show slash popover when / is first char") changed the `SLASH_TRIGGER_RE` regex in `apps/desktop/src/app/chat/composer/text-utils.ts`. The original regex `(?:^|[\\s])` allowed the popover to trigger when `/` appeared anywhere in the message (e.g. `"hello /"`), which didn't match execution semantics — slash commands only execute at the start of a message. The fix anchored the regex strictly at position 0 (`^`), so the popover only appears when `/` is the very first character.

## Discovery Process

1. Initially investigated shell completion (`hermes completion zsh`) — which was working fine.
2. User clarified the **desktop TUI popover** was the issue, not shell completion.
3. Found the offending commit via `git log` in the Hermes repo.
4. Desktop app build needed recompilation after the TypeScript change (`text-utils.ts` → bundled JS).

## Context

- Hermes Agent v0.19.0 (516 commits behind upstream)
- Shell completion (`hermes completion zsh`) unaffected — only the TUI slash popover was broken
- The `@`-mention trigger was deliberately left unchanged since mentions work anywhere
- See [[hermes-shell-completion]] for the shell-side completions
