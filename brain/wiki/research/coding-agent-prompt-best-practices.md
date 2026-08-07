---
source_session: 20260521_155536_3175a7
date: 2026-05-21
category: research
tags: [coding-agents, system-prompts, claude-code, aider, anthropic, best-practices]
---

# Coding Agent System Prompt Best Practices

Research across Anthropic docs, Claude Code plugins, Aider, Cursor/Windsurf community reports.

**Anthropic #1 principle:** give the agent a way to verify its work (tests, screenshots, expected outputs). Explore → Plan → Implement → Verify is canonical. CLAUDE.md: keep concise, only what the agent can't infer; if rules are ignored, the file is too long. Delegate research to subagents to keep main context clean.

**Claude Code plugin agents:** code-explorer (4-phase analysis: discovery, tracing, architecture, details; file:line refs), code-architect (one confident architectural choice + full blueprint), code-reviewer (confidence 0–100, report only ≥80).

**Aider:** EditBlock format (SEARCH/REPLACE with strict matching), WholeFile format; prompt modifiers lazy_prompt (never leave unimplemented comments) and overeager_prompt (only what's asked).

**Cross-agent patterns:** role definition, workflow phases, strict output format, verification instructions, scope constraints, confidence mechanisms, tool specification.

**Key insight:** verification loops — agents that run their own tests/linters and iterate outperform agents that stop after producing output.

[[opencode-prompt-architecture]] [[hermes-prompt-assembly]]
