---
category: software
source_session: 20260601_163349_f2b5c6
date: 2026-07-21
tags: [opencode, self-review, memory, skills, prompt-engineering]
---

# OpenCode Self-Review Setup

OpenCode has `memory`, `skill_manage`, and `skill_view` tools but lacks Hermes's daemon thread for auto-review after every turn. Three approaches provide functionally equivalent self-review:

## Approach 1: Prompt Module (inline, main context)

Add a `ReviewAfterTask` module to `~/.config/opencode/prompt.md` that fires after every complex task:

```markdown
## Module: ReviewAfterTask

fn on_task_complete:
  1. Review what was done — any new patterns, fixes, or corrections?
  2. If user corrected your approach/style/tone → update relevant SKILL.md
  3. If user revealed durable preference/environment fact → save with memory
  4. If a skill was wrong/outdated → patch it NOW with skill_manage(action='patch')
  5. Nothing worth saving → say nothing, move on
```

**Pro:** Always active. **Con:** Consumes tokens in main context.

## Approach 2: Standalone Skill (triggered on demand)

Create `~/.config/opencode/skills/self-review/SKILL.md` with the review protocol:

```yaml
name: self-review
description: Post-task review — save durable lessons to memory and skills
trigger: /review
```

Load with `skill_view('self-review')` or trigger with `/review` in TUI.

## Approach 3: Subagent (isolated context)

Add a `self-review` agent to `~/.config/opencode/opencode.json` with only file + terminal tools:
- Spawn via `delegate_task(goal="self-review", context=...)` at milestones
- Isolates review from main context like Hermes's daemon thread
- Uses the SKILL.md from Approach 2 as the canonical protocol reference

All three work together: the prompt module is the primary driver; when isolation is needed, it spawns the subagent; the skill file serves as the canonical reference.

## Related

- [[hermes-background-review-loop]]
- [[opencode-research-agent-setup]]
