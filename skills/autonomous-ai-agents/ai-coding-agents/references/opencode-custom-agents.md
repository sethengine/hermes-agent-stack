# OpenCode Custom Agents: Creation & Prompt Design

OpenCode supports custom agents beyond the built-in `build`, `plan`, `general`, and `simple`. Custom agents get their own system prompt, tool permissions, model, and temperature — defined in `opencode.json` under the `agent` key.

## Agent Config Schema

```json
{
  "agent": {
    "agent-name": {
      "description": "When to use this agent (optional)",
      "prompt": "{file:./prompt-name.md}",
      "temperature": 0.2,
      "mode": "all",
      "tools": {
        "searxng": true,
        "playwright": true
      }
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `description` | Shown in agent selector UI |
| `prompt` | System prompt — supports `{file:./path.md}`, `{env:VAR}`, or inline string |
| `temperature` | 0.0–2.0 (lower = more deterministic) |
| `mode` | `"primary"` (TUI default), `"subagent"` (@agent only), `"all"` (both) |
| `tools` | MCP server toggles — keys must match MCP server names exactly |
| `model` | Optional model override (`provider/model-id`) |
| `variant` | Model variant (e.g. `"thinking"`) |
| `hidden` | Hide from @ autocomplete (boolean) |
| `steps` | Max agentic iterations (number) |

## Critical Design Principle: Match Prompt Style to Domain

The single biggest mistake when creating custom agents is reusing a coding-agent prompt template for a non-coding domain. Different domains need fundamentally different prompt styles. **Getting this wrong means the agent will produce structurally wrong output — not just suboptimal, but unusable.**

| Domain | Style | Key traits |
|--------|-------|-----------|
| **Coding** | Terse, action-first | CavemanMode, skip filler, tool-use-over-description, completion gates |
| **Research** | Verbose, educational | Rich prose, concept explanation, multi-layer depth, source transparency, engage user with options |
| **Planning** | Structured, risk-aware | Break into tasks, flag dependencies, identify unknowns, batch questions |
| **Review** | Critical, evidence-based | Hypothesis investigation, forbidden hedges, cite line numbers, security scanning |

**Pitfall (concrete)**: A research agent with CavemanMode-style terseness will produce bare bullet points with no explanation, no context, no concept teaching, and no narrative — the user gets a list of facts they could have Googled instead of an educational research experience. **A research chatbot must be verbose, structured, and comprehensive — like a good research librarian, not a code-review bot.** The user will explicitly reject terse research output and ask you to rewrite the prompt. Conversely, a coding agent with verbose educational prose will waste context-window tokens on explanations instead of writing code.

**Pitfall (opposite direction)**: Giving a coding agent a verbose/educational prompt wastes the context window on prose the user doesn't need — they want code, not lectures. Each domain has its own optimal verbosity level.

## Example: Research Agent

Uses `{file:./prompt-research.md}` with these design choices:

- **Persona**: Expert research librarian + passionate educator
- **Depth**: Multi-layer explanation (ELI5 → layperson → technical → expert)
- **Output**: 8-section structured format (Overview, Exploration, Data, Perspectives, Implications, Unknowns, Further, Sources)
- **User engagement**: Proactive question tool usage with 2-4 concrete, actionable options
- **Domain adaptability**: Explicit handling for science, history, tech, philosophy, practical, comparison, current events
- **Anti-patterns**: Explicit forbidden list — no terse answers, no bullet-only, no hiding uncertainty

MCP tools enabled: searxng, brave-search, youtube-transcript, playwright, context7, c4ai, crawl, github

Activate: `opencode --agent research` or `/research` in TUI

## Prompt Module Architecture

The best agentic prompts use a pseudocode module format (from cli-agent-surgery):

```
## Module: ModuleName
fn function_name(input):
  rule = value
  never do_x
  always do_y
```

Benefits over prose:
- 3-5x more compact (critical for context window budget)
- Parseable — modules are self-contained, easy to add/remove
- Maintainable — one module's rules don't leak into another
- Testable — you can reason about each module independently

## Anti-Patterns Module (Recommended for Non-Coding Agents)

For agents where the prompt style is the opposite of what the base model might default to (e.g., a verbose research agent when the model tends toward brevity), include an explicit `AntiPatterns` or `forbidden` module listing what the agent must NEVER do. This is more effective than positive instructions alone — models are better at avoiding listed negatives than inferring style from positive descriptions.

Example for a research agent:
```
## Module: AntiPatterns (What NOT To Do)
forbidden:
  - short, terse responses with no explanation (you are NOT CavemanMode)
  - raw bullet lists without narrative context
  - single-sentence answers to complex questions
  - dumping search results without synthesis
  - presenting one side of a contested topic
  - overconfident claims on uncertain topics
  - skipping the "explain why this matters" step
```

This pattern applies to any domain where the prompt style runs counter to the model's default tendencies.

## Path Resolution for `{file:...}`

- `{file:./path.md}` — relative to `opencode.json` directory (`~/.config/opencode/`)
- `{file:~/path.md}` — expands `~` to home directory
- `{file:/absolute/path.md}` — absolute path
- `{env:VAR_NAME}` — environment variable

## Skills vs Agents

| Concept | What | Where |
|---------|------|-------|
| **Agent** | Has its own system prompt, tools, temperature, model. Controls *how* the LLM behaves. | `opencode.json` → `agent` key |
| **Skill** | Injects domain instructions into context (workflows, API refs, pitfalls). Controls *what* the LLM knows. | `~/.config/opencode/skills/<name>/SKILL.md` |

A custom agent can (and should) load skills. Skills auto-discover from the skills directory. The agent's prompt replaces the built-in provider prompt; AGENTS.md/CLAUDE.md and skills are appended after.

## Verification

After creating a custom agent, smoke-test:

```bash
# 1. Does it load?
opencode run --agent <name> 'Respond with exactly: AGENT_SMOKE_OK'

# 2. Can it use its MCP tools?
opencode run --agent <name> 'Search the web for "test" using searxng'

# 3. Does it follow its prompt style?
opencode run --agent <name> 'Explain quantum computing'
```

Success criteria: agent loads without errors, MCP tools connect, output style matches prompt design.
