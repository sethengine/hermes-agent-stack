---
source_session: 20260804_222206_b83689
date: 2026-08-04
category: software
tags: [hermes, memory, user-md, memory-md, char-limit, profile-budget, config]
related: [memory_systems_overview, hermes_system_prompt_management, brain_commands_reference, global_session_brain]
---

# Hermes Memory Char Limits — MEMORY.md vs USER.md Budgets

Hermes injects two files into every system prompt: **MEMORY.md** (agent's operating
knowledge) and **USER.md** (model of the user). Their budgets are configurable via
`config.yaml` `memory:` section:

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  write_approval: false
  memory_char_limit: 2200     # MEMORY.md cap
  user_char_limit: 1375       # USER.md cap
  provider: builtin
```

## UI mapping (Hermes Desktop)
- `memory.memory_char_limit` → "Memory Budget" (MEMORY.md)
- `memory.user_char_limit` → **"Profile Budget"** (USER.md) — the field labeled
  "Profile Budget" in Settings → Memory IS the USER.md limit.

Set via CLI equivalently: `hermes config set memory.user_char_limit 1800`
(respectively `memory.memory_char_limit`).

## Cost model
MEMORY.md + USER.md ≈ 2200+1375 ≈ 3.6K chars ≈ **~900 tokens of permanent overhead per
LLM call, every turn**, before the conversation starts. They sit in the system prompt so
every char is paid for on every request. On a small/fast model (e.g. deepseek-v4-flash)
a bloated memory competes with the task for attention. Prompt caching means the system
prompt is cached, so this overhead is largely constant/amortized across turns, not
variable — but raising the cap raises that constant.

To raise a cap, edit the corresponding key (or the GUI "Profile Budget" field).

## Related
- [[memory_systems_overview]] — the two memory files in detail
- [[hermes_system_prompt_management]]
- [[brain_commands_reference]]