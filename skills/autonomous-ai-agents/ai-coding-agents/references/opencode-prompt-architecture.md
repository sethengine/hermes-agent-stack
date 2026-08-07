# OpenCode Prompt Architecture

Full details on how OpenCode assembles system prompts and configures agents.

## Prompt Assembly Flow

When a user sends a message, the system prompt is assembled in `src/session/prompt.ts`:

```
system = [...env, ...instructions, ...(skills ? [skills] : [])]
```

1. **env** — `SystemPrompt.environment(model)` → working dir, workspace root, platform, date, model name
2. **instructions** — `Instruction.system()` → loads AGENTS.md, CLAUDE.md, CONTEXT.md, plus config `instructions` paths
3. **skills** — `SystemPrompt.skills(agent)` → lists available skills (if agent has skill permission)

The agent's `prompt` field is NOT injected into the system array here — it's used by the `Agent` service and passed as part of the agent definition. For built-in agents (build, plan, general), the provider-specific prompt from `src/session/prompt/` is the default.

## Built-in Provider-Specific Prompts

OpenCode ships different prompts per model family in `src/session/prompt/`:

| File | Used For |
|------|----------|
| `default.txt` | Default/fallback models |
| `anthropic.txt` | Claude models |
| `gpt.txt` | GPT models |
| `beast.txt` | GPT-4, o1, o3 models |
| `codex.txt` | GPT Codex models |
| `gemini.txt` | Gemini models |
| `kimi.txt` | Kimi models |
| `trinity.txt` | Trinity models |

Selection logic in `src/session/system.ts` checks `model.api.id` string patterns.

## Subagent Prompts

Subagent prompts live in `src/agent/prompt/`:

| Agent | Prompt File | Purpose |
|-------|-----------|---------|
| `explore` | `explore.txt` | Fast codebase search agent |
| `scout` | `scout.txt` | External docs/dependency research |
| `compaction` | `compaction.txt` | Context compression/summarization |
| `title` | `title.txt` | Generate session titles |
| `summary` | `summary.txt` | Create session summaries |

`build` and `plan` agents don't have their own prompt files — they use the provider-specific prompt from the system prompt module.

## Agent Configuration Schema

From `src/config/agent.ts`:

| Field | Type | Description |
|-------|------|-------------|
| `model` | string (`provider/model-id`) | Model override |
| `variant` | string | Model variant (e.g., "thinking") |
| `prompt` | string | System prompt (supports `{file:...}` in JSON) |
| `description` | string | When to use this agent |
| `temperature` | number | LLM temperature |
| `top_p` | number | Nucleus sampling |
| `mode` | "primary" \| "subagent" \| "all" | Agent visibility mode |
| `hidden` | boolean | Hide from @ autocomplete |
| `permission` | object | Tool permissions (allow/ask/deny) |
| `steps` | number | Max agentic iterations |
| `color` | string | Hex color or theme color for UI |
| `options` | object | Extra provider-specific params |

## `{file:...}` Variable Substitution

Resolved by `ConfigVariable.substitute()` in `src/config/variable.ts`:

- **Format**: `{file:./relative/path.txt}`, `{file:~/path/to/file}`, `{file:/absolute/path}`
- **Scope**: Only in `opencode.json` / `opencode.jsonc` config files
- **Resolution**: Paths relative to config file directory. `~/` expands to home. Absolutes start with `/`.
- **Also supports**: `{env:VAR_NAME}` for environment variable substitution
- **Regex**: `/{file:[^}]+}/g` — matches `{file:` followed by any chars up to `}`
- **Error handling**: If file missing and `missing` mode is `"error"`, throws. If `"empty"`, returns empty string.

## Instruction Files (AGENTS.md / CLAUDE.md)

The `Instruction` service (`src/session/instruction.ts`) loads from:

- **Global**: `~/.config/opencode/AGENTS.md` and `~/.claude/CLAUDE.md`
- **Project**: Walks upward from cwd to workspace root, finds first `AGENTS.md`, `CLAUDE.md`, or `CONTEXT.md`
- **Config `instructions` array**: Paths/globs or URLs specified in `opencode.json`

All are prefixed with `"Instructions from: <path>\n"` and injected into the system prompt array.

## Research-Backed System Prompt Patterns

The best agentic system prompts (from Claude Code, Aider, cli-agent-surgery, promptPrimer) share these patterns:

1. **Pseudocode module format** — Declarative constraints compress 3-5x better than prose. Named modules (CavemanMode, QualityStandard) make prompts parseable and maintainable.

2. **Autonomy block** — "Decide-document-proceed on reversible choices. Only 3 ask-now triggers: irreversible+missing-info, scope violation, plan invalidated."

3. **Context preservation** — Session opening protocol (read STATE/todo/AGENTS.md first), post-compaction recovery, filesystem-beats-context principle.

4. **Hypothesis investigation** — Forbidden hedge list, evidence escalation ladder, treat intuition as hypothesis-not-conclusion.

5. **Verification loops** — Always run tests/lints/builds after changes. Self-review diffs. Completion gate: tests pass, lint pass, no new warnings.

6. **Tool preference** — Dedicated tools > shell for file operations. `read_file` not `cat`, `patch` not `sed`, `search_files` not `grep`.

7. **Output efficiency** — Lead with answer/action, skip filler/preamble, batch questions, never restate user message.

Key sources:
- [OxideDall/cli-agent-surgery](https://github.com/OxideDall/cli-agent-surgery) — Pseudocode module architecture, hypothesis investigation, quality standard
- [SeidSmatti/promptPrimer](https://github.com/SeidSmatti/promptPrimer) — Autonomy block, context preservation, STATE.md
- [GAIn-Tech/opencode-setup](https://github.com/GAIn-Tech/opencode-setup) — OpenCode AGENTS.md patterns, context budget thresholds
- [Anthropic Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) — Explore→Plan→Implement→Verify, verification loops
- [Aider](https://github.com/Aider-AI/aider) — Edit format discipline, scope constraints