---
category: software
source_session: 20260426_124701_f4d2b9
date: 2026-07-21
tags: [hermes, soul, agents, prompt-assembly, architecture]
---

# Hermes Prompt Assembly: SOUL.md vs AGENTS.md

Hermes builds its system prompt from multiple sources in a fixed hierarchy:

## Slot 1: SOUL.md (global, personality)

Loaded from `~/.hermes/SOUL.md`. Strictly for **agent identity/personality** (tone, style, voice). Always loaded, independent of project. Capped at ~20k chars. Auto-seeded if missing.

## Slot 2: Project context files (local, project-specific)

Discovered from CWD at startup + subdirectories. Priority order (first match wins):
1. `.hermes.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `.cursorrules`

Loaded under "# Project Context". Not probed from `$HERMES_HOME` — strictly cwd-bound.

## Design Intent

| File | Scope | Purpose |
|------|-------|---------|
| SOUL.md | Global | Persona, voice, cross-project behavior |
| AGENTS.md | Project-local | Architecture, conventions, workflows |

## Workarounds for "Global" Instructions Beyond Personality

1. **SOUL.md** — OK for stable cross-project instructions, but keep personality-focused.
2. **Memory tool** — User/environment facts injected every turn (see [[hermes-background-review-loop]]).
3. **Skills** — Preload with `hermes --skills skill1,skill2` or load in-session.
4. **config.yaml** — `agent.system_prompt` for custom overlays.
5. **Cwd hack** — Always run Hermes from `~/global-agents/` dir with an AGENTS.md.

## Related

- [[hermes-system-prompt-management]]
- [[hermes-background-review-loop]]
- [[hermes-soul-md-opencode-conversion]]
