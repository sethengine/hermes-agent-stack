---
source_session: 20260521_155951_a5c4dc
extracted_date: 2026-07-22
category: software
tags: [opencode, prompts, system-prompt, architecture, configuration]
---

# OpenCode System Prompt Architecture

OpenCode's system prompt for each LLM call is assembled from multiple components in a specific order.

## Prompt Assembly Flow

1. **Provider-specific prompt**: Selected by model type (`src/session/system.ts`) from text files in `src/session/prompt/`
2. **Environment info**: Injected dynamically (working dir, workspace root, platform, date, model name)
3. **Instructions**: Loaded from `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md` files plus `instructions` paths in `opencode.json`
4. **Skills**: Listed if the agent has the `skill` permission enabled

Final array: `system = [...env, ...instructions, ...(skills ? [skills] : [])]`

## Provider-Specific Prompts

| File | Used For |
|------|----------|
| `default.txt` | Default/fallback |
| `anthropic.txt` | Claude models |
| `gpt.txt` | GPT models |
| `beast.txt` | GPT-4, o1, o3 |
| `codex.txt` | GPT Codex |
| `gemini.txt` | Gemini |
| `kimi.txt` | Kimi |
| `trinity.txt` | Trinity |

## Subagent Prompts

Stored in `src/agent/prompt/` — `explore`, `scout`, `compaction`, `title`, `summary` agents each have dedicated prompt files. The `build` and `plan` agents use the provider prompt directly.

## `{file:./path}` Template Syntax

Resolved by `ConfigVariable.substitute()` in `src/config/variable.ts`. Supports `{file:./relative/path}`, `{file:~/path}`, `{file:/absolute/path}`, and `{env:VAR_NAME}`. Only works in `opencode.json`/`opencode.jsonc`, not inside markdown agent files.

## Agent Configuration Fields

From `src/config/agent.ts`: `model`, `variant`, `prompt`, `description`, `temperature`, `top_p`, `mode` (primary/subagent/all), `hidden`, `permission` (allow/ask/deny per tool), `disable`, `steps` (max iterations), `color`, `options`.

## Custom Agent Prompt Methods

**JSON config**: `"prompt": "You are a code reviewer..."` in `opencode.json`. **Markdown files** in `.opencode/agents/` or `~/.config/opencode/agents/` use YAML frontmatter for config and body as prompt text.
