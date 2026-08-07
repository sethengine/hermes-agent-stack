---
source_session: 20260521_155127_243604
date: 2026-05-21
category: software
tags: [opencode, system-prompt, agentic, cli-agent-surgery, promptprimer]
---

# OpenCode System Prompt Optimization

OpenCode's system prompt was rebuilt by synthesizing 5 sources: OxideDall/cli-agent-surgery, SeidSmatti/promptPrimer, Anthropic Claude Code docs, Aider prompts, and community consensus.

## Files (all in ~/.config/opencode/)

- `prompt.md` — new comprehensive prompt (19 KB), referenced by the `power` agent via `{file:./prompt.md}`
- `prompt.md.bak` — old prompt backup (12.1 KB); restore with `cp prompt.md.bak prompt.md`
- `prompt.txt` — older 27 KB variant
- `AGENTS.md` — new project-level context file for cross-session persistence
- `opencode.json` — power agent now has all tools enabled

## Key Patterns Adopted

- **Pseudocode module format** (cli-agent-surgery): declarative modules compress 3-5x better than prose — CavemanMode (3-sentence max), HypothesisInvestigation (forbidden hedges, evidence ladder, intuition-as-hypothesis), QualityStandard (PRODUCTION, no TODOs), ExecutingActions (risky-action confirmation)
- **Autonomy block** (promptPrimer): decide-document-proceed, only 3 "ask now" triggers, investigate-before-asking
- **Context preservation**: session opening protocol, post-compaction recovery, filesystem-beats-context
- **Explore → Plan → Implement → Verify** phases with verification loops as #1 leverage
- **Edit discipline** (Aider): read before modify, scope constraint (no surrounding cleanup)

Activate with: `opencode --agent power`

See also: [[coding-agent-prompt-best-practices]], [[opencode-prompt-architecture]], [[opencode-research-agent-setup]]
