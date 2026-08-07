---
source_session: "20260704_133636_461f0c"
extracted_at: "2026-07-04T11:06:41+00:00"
category: software
tags: [hermes, tui, bug, slash-command, save]
---

# Hermes TUI `/save` Slash Command Bug

The `/save` slash command in the Hermes desktop TUI app returns `"(;_;) No conversation to save."` even when a conversation is active.

## Root Cause

The TUI routes slash commands through a **slash worker subprocess** (`slash_worker.py`). This subprocess creates a fresh `HermesCLI` instance with `conversation_history = []` — it never loads the actual session messages from the session DB. Meanwhile, the real conversation history lives in the **TUI server process** memory (`session["history"]`), which the slash worker has no access to.

The TUI server actually has a working `session.save` RPC handler (in `tui_gateway/server.py`) that properly saves from the real history. But the `/save` **slash command** bypasses this and goes through the CLI slash worker subprocess instead — a routing disconnect.

## Impact

Affected commands: `/save`, likely also `/history` and any slash command that depends on `conversation_history`.

## Workaround

1. Messages are already persisted incrementally to the SQLite session DB (`~/.hermes/state.db`) as you chat — nothing is lost. Sessions are resumable via session ID.
2. For JSON export: use `hermes sessions list` then `hermes sessions export <ID>`.
3. In CLI mode (terminal, not desktop app), `/save` works correctly because the CLI has the conversation in its own memory.

[[hermes-tui-architecture]] [[hermes-slash-commands]] [[hermes-session-storage]]
