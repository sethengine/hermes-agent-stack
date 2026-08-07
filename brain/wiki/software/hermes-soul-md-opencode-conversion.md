---
source_session: 20260425_170324_3f10d9
extracted_date: 2026-07-17
category: devops
tags: [hermes, opencode, soul-md, system-prompt, tool-mapping]
---

# Converting OpenCode prompt.md to Hermes SOUL.md

OpenCode's `prompt.md` (~88KB, 1079 lines) was adapted to serve as Hermes' primary SOUL.md at `~/.hermes/SOUL.md`.

## Critical tool renames

| OpenCode | Hermes |
|----------|--------|
| Bash | `terminal(command=...)` |
| Read | `read_file(path=...)` |
| Edit / MultiEdit | `patch(path=..., replace_all=true)` |
| Write | `write_file(path=...)` |
| Glob / Grep / LS | `search_files(target='files'/'content')` |
| TodoWrite | `todo(todos=[...])` |
| AskUserQuestion | `clarify(...)` |
| Task | `delegate_task(goal=...)` |
| WebFetch / WebSearch | `mcp_searxng_web_url_read` / `mcp_searxng_web_search` |
| BashOutput / KillBash | `process(poll)` / `process(kill)` |

## Schema fixes

- Todo enum: added `"cancelled"` status
- Read format note: `LINE_NUM|` prefix (not raw `cat -n`)

## Hermes enhancements added

- Skills (`/skill <name>`) and auto-saving
- Memory / `session_search` for cross-session recall
- MCP tool prefix pattern (`mcp_playwright_*`, `mcp_searxng_*`)
- Tool enforcement: call immediately, no "I will..."
- Duplicate todo sections merged (~15% trim)

## Backup preserved

Original SOUL.md at `~/.hermes/SOUL.md.backup`. Activate with `/reset`.

See [[hermes-system-prompt-management]] for personality and skill alternatives.
