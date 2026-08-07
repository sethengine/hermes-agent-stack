---
category: software
source_session: 20260601_163349_f2b5c6
date: 2026-07-21
tags: [hermes, architecture, memory, skills, background-review]
---

# Hermes Background Review Loop

Hermes fires a **daemon thread** after every conversation turn that reviews the exchange and updates memory/skills automatically — a "self-improvement loop."

## Architecture

The loop lives at `agent/background_review.py`. After each assistant response:

1. **Fork** — Creates a mini `AIAgent` copy inheriting the same provider, model, and cached system prompt (hits prefix cache — no added latency on the main conversation).
2. **Review** — The forked agent gets review prompts that check for:
   - User persona/preference/environment details worth saving to memory
   - Skill-worthy lessons (fixes, patterns, corrections)
   - Outdated or wrong skills that need patching
3. **Act** — The fork has a restricted toolset (only `memory` + `skill_manage`). It writes durable facts to the memory store and creates/patches SKILL.md files in `~/.hermes/skills/`.
4. **Report** — Output appears as `💾 Self-improvement review: Memory updated` (or `Skill updated`), attributed to the background fork.

## Memory vs Skills vs User Profile

| Store | Tools | Content |
|-------|-------|---------|
| **Memory** (`memory` tool, `target='memory'`) | `memory` | Environment facts, tool quirks, conventions |
| **User profile** (`memory` tool, `target='user'`) | `memory` | User identity, preferences, recurring corrections |
| **Skills** (`skill_manage`) | `skill_manage` | Full SKILL.md documents with procedures, pitfalls, templates |

**What SHOULD go in memory:** User preferences, environment details, tool quirks, stable conventions.
**What MUST NOT go in memory:** Task progress, PR numbers, commit SHAs, session artifacts — any fact stale in < 7 days.

## Related

- [[hermes-system-prompt-management]]
- [[opencode-self-review-setup]]
