# Porting the System-Spec Reference Skill to OpenCode

Case study: porting the `system-spec` skill (comprehensive HW/SW inventory with live-checked data) from Hermes to OpenCode.

## Source (Hermes)

`~/.hermes/skills/devops/system-spec/SKILL.md` — rich YAML frontmatter with `version`, `author`, `license`, `platforms`, `tags`, `metadata.hermes`, `description`:

```yaml
---
name: system-spec
category: devops
description: >-
  Full hardware + software specification for sethengine's workstation.
  Rewrite this skill's spec section when any component changes.
tags: [system-spec, hardware, software, linux, gaming, nvidia, manjaro]
# Also had version, author, etc.
---
```

Body includes: system overview, motherboard/BIOS, CPU, GPU, memory, storage, display, audio, input, network, kernel params, software versions, **quick verification commands** (`cat /proc/cpuinfo`, `nvidia-smi`, `inxi -Fxz`), and a `skill_manage(action='patch')` update workflow.

## Target (OpenCode)

`~/.config/opencode/skills/system-spec/SKILL.md` — minimal YAML frontmatter:

```yaml
---
name: system-spec
description: >-
  Full hardware + software specification for sethengine's workstation.
  Load this skill whenever system details are relevant — debugging,
  gaming advice, performance tuning, driver questions, kernel config.
---
```

Body keeps all the same spec data and verification commands. Only the update workflow changes.

## Key Adaptations

| Aspect | Hermes | OpenCode | Notes |
|--------|--------|----------|-------|
| Frontmatter | Rich (version, author, tags, metadata) | `{name, description}` only | Strip all extra fields |
| Tool refs | `skill_manage(action='patch', name='system-spec', ...)` | `edit` tool for targeted field replacement | OpenCode has no `skill_manage` — use its native `edit` |
| Skill path | `~/.hermes/skills/<category>/<name>/` | `~/.config/opencode/skills/<name>/` | OpenCode doesn't use category subdirectories |
| Auto-discovery | Description + tags trigger `skill_view(name)` on relevant topics | Description alone triggers auto-load | OpenCode doesn't use tags — description must be broad enough |
| Update commands | `skill_manage(action='patch', old_string=..., new_string=...)` | `edit <path>` with old/new string | Both use find-and-replace pattern |

### What Stayed the Same

- All HW/SW spec data (identical content)
- Quick verification commands (shell commands, platform-agnostic)
- Structure: tables for each component, GRUB cmdline as code block, etc.

### What Was Stripped

- Hermes-specific `version`, `author`, `license`, `platforms` YAML fields
- `metadata.hermes` block
- `tags` array (OpenCode uses description as the sole trigger)
- `related_skills` references (Hermes cross-linking concept)

## Why This Pattern Ports Well

**Reference/spec skills** (static data + verification commands) are the easiest class to port across platforms because:

1. **Data is platform-agnostic** — hardware specs, kernel params, GRUB lines are the same regardless of agent
2. **Verification commands are shell commands** — work on any agent with a terminal/bash tool
3. **No orchestration logic** — no `delegate_task`, no subagent spawning, no process management
4. **Minimal tool dependencies** — only need `read_file`/`write_file`/`edit` equivalents

Compare to **orchestration skills** (like the review loop in `references/hermes-review-to-opencode-port.md`) which need significant adaptation because they rely on platform-specific concurrency models.

## Verification

```bash
# Hermes version
ls ~/.hermes/skills/devops/system-spec/SKILL.md
python3 -c "import yaml; d=yaml.safe_load(open('/home/sethengine/.hermes/skills/devops/system-spec/SKILL.md')); print(d['name'], d.get('tags'))"

# OpenCode version
ls ~/.config/opencode/skills/system-spec/SKILL.md
python3 -c "import yaml; d=yaml.safe_load(open('/home/sethengine/.config/opencode/skills/system-spec/SKILL.md')); print(d['name'], d['description'][:60])"

# Verify data integrity — both should contain the same specs
grep -c "RTX.*5060\|Ultra 7\|Z890" ~/.hermes/skills/devops/system-spec/SKILL.md ~/.config/opencode/skills/system-spec/SKILL.md
```
