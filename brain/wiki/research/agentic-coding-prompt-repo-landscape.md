---
source_session: 20260521_155344_60808d
date: 2026-05-21
category: research
tags: [opencode, system-prompts, github-repos, prompt-engineering, research]
---

# Agentic Coding Prompt Repo Landscape

Five GitHub repos were cloned and analyzed for agentic coding-assistant system prompts (full analysis: `/home/sethengine/extracted-system-prompts.md`).

## Repos

- **GAIn-Tech/opencode-setup** — OpenCode config ecosystem; its `AGENTS.md` shows anti-pattern classification (CRITICAL > HIGH > WARNING), context-budget thresholds, and WHERE TO LOOK tables
- **SeidSmatti/promptPrimer** — meta-prompt generation; `<autonomy>` and `<context_preservation>` blocks are the most transferable patterns (minimize round-trips, survive context compaction)
- **kzhekov/Prompt-Engineering-Skill** — 6-module router skill with 16-item design checklist and debugging tables
- **OxideDall/cli-agent-surgery** — most complete prompt found: 532-line `system_prompt.md`, 12+ pseudocode modules, `{{PLACEHOLDER}}` template vars, explicit `opencode.json` agent integration
- **matteocervelli/llms** — LLM config/skill template tooling, not prompt-focused

## Top Patterns for OpenCode

1. Pseudocode module format
2. Autonomy + context-preservation blocks
3. STATE.md with fixed schema for cross-session continuity
4. Forbidden-hedge lists, evidence-based reasoning
5. Quality gates as assert-like statements
6. Type-module system per task type
7. Dedicated tools over raw shell
8. Test prompts at turn 50, not turn 1
9. Critical instructions at prompt start AND end
10. Wrap dynamic content in labeled tags; treat as untrusted

See also: [[opencode-system-prompt-optimization]], [[coding-agent-prompt-best-practices]]
