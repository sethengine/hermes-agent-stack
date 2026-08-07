---
source_session: 20260425_170324_3f10d9
extracted_date: 2026-07-17
category: devops
tags: [hermes, configuration, personalities, prompts, skills]
---

# Managing System Prompts in Hermes Agent

Hermes builds its system prompt dynamically each turn. The main overrideable part is the **personality**.

## Changing personality

In-session (temporary): `/personality pirate` — resets on session end.
Persistent: `hermes config set display.personality technical`

Available personalities: `helpful`, `concise`, `technical`, `creative`, `teacher`, `kawaii`, `catgirl`, `pirate`, etc.

## Custom personalities

Add to `~/.hermes/config.yaml` under `agent.personalities`:

```yaml
agent:
  personalities:
    mycustom: |
      You are an expert coder. Always think step-by-step.
      Never say "as an AI". Be concise.
```

Then activate with `hermes config set display.personality mycustom`.

## Long prompts without bloating YAML

For large prompts (e.g. 88KB OpenCode prompt), use one of:

1. **SOUL.md** — `cp ~/.config/opencode/prompt.md ~/.hermes/SOUL.md` — auto-loads as primary identity. See [[hermes-soul-md-opencode-conversion]].
2. **Skills** — `~/.hermes/skills/custom/<name>/SKILL.md` — `/skill <name>` in-session.
3. **Prefill messages** — `hermes config set prefill_messages_file ~/.hermes/start.jsonl`

## Profiles

Isolated configs: `hermes profile create coder` → `hermes -p coder`
