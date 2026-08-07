# Porting Hermes Background Review to OpenCode

Case study: replicating Hermes's `agent/background_review.py` daemon on
OpenCode (v1.15.13).

## Source (Hermes)

`agent/background_review.py` — after every conversation turn, spawns a
daemon thread that forks the agent, replays the conversation snapshot, and
reviews for memory + skill updates. Runs with a restricted tool whitelist
(memory + skill_manage only), never touches main context or prompt cache.

## OpenCode Capability Gap

OpenCode has `memory`, `skill_manage`, and `skill_view` tools (via
`opencode-agent-memory` plugin) but **no background daemon thread** — the
model must self-initiate review.

## Implementation (3-Layer Approach)

### Layer 1: Prompt Injection (highest reliability)

Patch the agent's prompt (`~/.config/opencode/prompt.md` for the `power`
agent) with a `ReviewAfterTask` module that mirrors the Hermes review
prompts. This runs inline after complex tasks, user corrections, or
session milestones.

Key design: same 3-step flow (memory scan → skill scan → declare), same
4-step preference order (loaded skill → umbrella → support file → new
class-level), same pitfall list (no env-dependent failures, no negative
tool claims, no one-off narratives).

### Layer 2: Standalone Skill

Create `~/.config/opencode/skills/self-review/SKILL.md` with YAML
frontmatter (`name`, `description`, `trigger: /review`). Full-detail
version of the review protocol. Triggerable via `/review` in TUI or
loadable via `skill_view`. Serves as canonical reference.

### Layer 3: Subagent (closest to Hermes fork)

Register a `self-review` agent in `~/.config/opencode/opencode.json`:

```json
"self-review": {
  "prompt": "You are a post-task self-improvement review agent...",
  "temperature": 0.3,
  "tools": { all disabled except file + terminal },
  "mode": "subagent"
}
```

Subagent-only mode with search/browser tools disabled — mirrors Hermes's
restricted tool whitelist. The parent agent spawns it via `delegate_task`
at milestones, isolating review from main context.

### How They Complement

| Layer | Fires | Context cost | Isolation |
|-------|-------|-------------|-----------|
| Prompt module | Inline, every complex task | High (in main ctx) | None |
| Skill | On-demand via `/review` | Medium (loaded into ctx) | None |
| Subagent | `delegate_task` at milestones | Low (summary only) | Full (Hermes-like fork) |

The prompt module is the primary driver (always-on). The subagent is the
escalation path for expensive reviews. The skill is the reference document
any agent can load.

## File Locations

| What | Where |
|------|-------|
| Prompt (Layer 1) | `~/.config/opencode/prompt.md` |
| Skill (Layer 2) | `~/.config/opencode/skills/self-review/SKILL.md` |
| Agent config (Layer 3) | `~/.config/opencode/opencode.json` |
| Memory store | `~/.opencode/memory/` (plugin: opencode-agent-memory) |

## Verification

```bash
# Check skill discovery
ls ~/.config/opencode/skills/self-review/SKILL.md

# Check agent registration
grep -A10 '"self-review"' ~/.config/opencode/opencode.json

# Check prompt module
grep -A5 'ReviewAfterTask' ~/.config/opencode/prompt.md
```
