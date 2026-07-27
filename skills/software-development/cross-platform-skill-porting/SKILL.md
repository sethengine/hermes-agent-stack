---
name: cross-platform-skill-porting
description: Port skills and conventions between AI agent platforms (Hermes, OpenCode, Claude Code) — format differences, tool mappings, adaptation patterns.
---

# Cross-Platform Skill Porting

Port skills between AI agent platforms — Hermes Agent, OpenCode, Claude Code, and similar coding agents. Each platform has its own skill format, tool vocabulary, and agent model. This skill captures the mappings and patterns.

## When to Use

- User asks to copy/migrate skills from one platform to another
- Setting up a new agent platform and want to carry over existing skills
- User runs multiple agents and wants consistent behavior across them
- You discover a new platform's skill system and need to adapt existing skills

## Platform Skill Systems at a Glance

| Platform | Skill Location | Format | Discovery |
|----------|---------------|--------|-----------|
| **Hermes** | `~/.hermes/skills/<category>/<name>/SKILL.md` | Rich YAML frontmatter (version, author, tags, related_skills, prerequisites, metadata) | `skill_view()` in system prompt |
| **OpenCode** | `~/.config/opencode/skills/<name>/SKILL.md` | Simple YAML frontmatter (name, description, trigger) | Auto-loaded from directory |
| **OpenCode (alt)** | `~/.claude/skills/<name>/SKILL.md` | Same simple format | Shared with Claude Code |
| **Claude Code** | `~/.claude/skills/<name>/SKILL.md` | Same simple format | Auto-loaded from directory |
| **Claude Code (proj)** | `.claude/skills/<name>/SKILL.md` | Same | Per-project |

### OpenCode Skill Discovery (verified on v1.15.5)

OpenCode discovers skills from two directories:
1. `~/.config/opencode/skills/<name>/SKILL.md` — user-level OpenCode skills
2. `~/.claude/skills/<name>/SKILL.md` — shared with Claude Code (compatibility layer)

OpenCode also loads `AGENTS.md` or `CLAUDE.md` from project roots for per-project context.

The `trigger` field in frontmatter registers an optional slash command (e.g., `trigger: /arxiv` → `/arxiv` in TUI).

OpenCode also has a separate **agents** system (configured in `opencode.json`) with permission-gated subagents: `build`, `plan`, `explore`, `general`, `power`, `simple`. Agents are different from skills — agents control tool permissions, skills inject instructions into context.

## Porting Procedure

### Step 1: Load the source skill

Read the Hermes SKILL.md fully to understand what it does.

### Step 2: Identify what to keep vs. strip

**Keep:**
- Core methodology and instructions
- Domain knowledge (API endpoints, CLI flags, conventions)
- Workflows and procedures
- Pitfalls and gotchas

**Strip:**
- Hermes-specific YAML frontmatter fields (version, author, license, platforms, metadata)
- Hermes-specific tool references (see tool mapping below)
- Hermes-specific agent concepts (`delegate_task`, `skill_view`, `read_file`)

**Adapt:**
- Frontmatter to `{name, description, trigger?}` format
- Tool references to target platform equivalents
- Agent/delegation concepts to target platform equivalents
- Directory paths and conventions

### Step 3: Apply the tool mapping

| Hermes Tool | OpenCode Equivalent | Notes |
|-------------|-------------------|-------|
| `read_file(path)` | `cat path` or `read` tool | OpenCode's `read` is its native file tool |
| `search_files(pattern, target="content")` | `grep -rn "pattern" path/` | Or OpenCode's `grep` tool |
| `search_files(pattern, target="files")` | `find path/ -name "pattern"` or `glob` tool | Or OpenCode's `glob` tool |
| `terminal(command)` | `bash` command | OpenCode's bash tool |
| `write_file(path, content)` | `write` tool | Or `cat > file << 'EOF'` in bash |
| `patch(path, old, new)` | `edit` tool | OpenCode's native edit tool |
| `delegate_task(goal, context)` | `@agent` mentions in OpenCode | OpenCode dispatches subagents via @mentions |
| `web_extract(urls=[...])` | `webfetch` tool | OpenCode's web fetch |
| `web_search(query)` | `websearch` tool | OpenCode's web search |
| `vision_analyze(image)` | Native vision | OpenCode has built-in vision |
| `execute_code(code)` | `bash` with python3 | Use bash to run Python scripts |
| `clarify(questions)` | `question` tool | OpenCode's user question tool |
| `todo(todos)` | `todowrite` tool | OpenCode's task tracking |
| `skill_view(name)` | N/A | OpenCode auto-loads all skills in directory |
| `memory(action, ...)` | `~/.opencode/memory/` | OpenCode's persistent memory files |
| `process(action, session_id)` | N/A | OpenCode manages sessions differently |

### Step 4: Adapt agent/delegation concepts

**Hermes `delegate_task`:**
```python
delegate_task(goal="Fix bug X", context="...", toolsets=['terminal', 'file'])
```

**OpenCode equivalent (`@agent` mentions):**
```
@agent Fix bug X in src/auth.py. The error is: [paste error].
Use TDD: write failing test first, then fix.
```

OpenCode subagents are dispatched inline via `@agent` mentions. They run in parallel when multiple `@agent` mentions appear in the same response. Each gets its own context window.

### Step 5: Adapt paths and conventions

- `~/.hermes/` → `~/.config/opencode/` or `~/.opencode/`
- `~/.hermes/skills/` → `~/.config/opencode/skills/`
- Project context: Hermes uses its own prompt; OpenCode uses `AGENTS.md` / `CLAUDE.md`

### Step 6: Write and verify

```bash
mkdir -p ~/.config/opencode/skills/<skill-name>
# Write SKILL.md
```

Verify by listing: `ls ~/.config/opencode/skills/`

## Skill Format Templates

### Hermes Format (source)

```yaml
---
name: skill-name
description: "What this skill does"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: [other-skill]
---

# Skill Title
...
```

### OpenCode Format (target)

```yaml
---
name: skill-name
description: What this skill does and when to use it
trigger: /optional-slash-command
---

# Skill Title
...
```

## Skill Categories — What Ports Well vs. Doesn't

### Ports well (methodology + tool-usage guides)

- **Research skills**: arxiv, blogwatcher, llm-wiki — mostly curl/bash, tool-agnostic
- **Software methodology**: systematic-debugging, test-driven-development, writing-plans — pure process
- **Tool reference skills**: CLI flag references, API docs — platform-agnostic

### Needs significant adaptation

- **Agent orchestration skills**: claude-code, codex — Hermes-specific `terminal(pty=true)` and `process(action="submit")` patterns need rewriting for OpenCode's bash tool
- **Delegation skills**: subagent-driven-development — `delegate_task` → `@agent` mentions

### Doesn't port (platform-specific)

- **Hermes configuration**: hermes-agent skill — only relevant inside Hermes
- **Hermes CLI tools**: hermes-specific slash commands and workflows

## OpenCode System Prompt Configuration

OpenCode's system prompt for each LLM call is assembled from:
1. **Provider-specific prompt** (built-in, auto-selected by model)
2. **Environment info** (cwd, platform, date — auto-injected)
3. **Instruction files** (`AGENTS.md`, `CLAUDE.md`, `CONTEXT.md` — auto-loaded)
4. **Agent prompt override** (from `opencode.json` config)

Customize at three levels:

**Level 1: AGENTS.md** — Project-level context, auto-loaded from project root or `~/.config/opencode/AGENTS.md`. Use for coding conventions, architecture notes, project rules. Keep concise — if rules are ignored, the file is likely too long.

**Level 2: Agent config** — Override system prompt per agent in `opencode.json`:
```json
{
  "agent": {
    "power": {
      "prompt": "{file:./prompt.md}",
      "temperature": 0.3,
      "mode": "all",
      "tools": { "github": true }
    }
  }
}
```
`{file:./path}` reads a file relative to the config directory. `{env:VAR}` for env vars. The prompt replaces the built-in provider prompt for that agent.

**Level 3: Markdown agent files** — `~/.config/opencode/agents/<name>.md` with YAML frontmatter:
```markdown
---
description: Reviews code for quality
model: anthropic/claude-sonnet-4-20250514
temperature: 0.1
mode: subagent
permission:
  edit: deny
---
You are a code reviewer...
```

Key fields: `model`, `variant`, `prompt`, `description`, `temperature`, `top_p`, `mode` (primary/subagent/all), `hidden`, `permission`, `steps`, `color`, `options`.

## Creating Custom OpenCode Agents (End-to-End)

When building a custom agent beyond the built-in `build`/`plan`/`general`, follow this workflow:

### Step 1: Define the agent's purpose and tools

Decide what the agent does and which MCP servers it needs. Research agents need search+browse+tools; coding agents need file+terminal+tools.

### Step 2: Write the system prompt

Create a prompt file at `~/.config/opencode/prompt-<agent>.md`. Follow the module pattern — each module a focused concern, each rule a declarative constraint. Key modules for any custom agent:
- **CoreIdentity** — what the agent is and what it does
- **ToolRouting** — which tool for which task type
- **OutputFormat** — structured output expectations
- **Pitfalls/Safety** — what the agent must never do

For a working example covering 17 modules (research methodology, question-asking, source quality, verification integrity, tool routing, etc.), see `references/opencode-research-agent-prompt.md`.

### Step 3: Register in opencode.json

```json
{
  "agent": {
    "<agent-name>": {
      "prompt": "{file:./prompt-<agent>.md}",
      "temperature": 0.2,
      "description": "What this agent does and when to use it",
      "tools": {
        "searxng": true,
        "playwright": true,
        "brave-search": true
      },
      "mode": "all"
    }
  }
}
```

Key fields:
| Field | Purpose |
|-------|---------|
| `prompt` | `{file:./path}` loads from config dir; `{env:VAR}` for env vars |
| `temperature` | 0.1–0.3 for deterministic agents, 0.5–0.7 for creative |
| `tools` | Keys must match MCP server names in the `mcp` section exactly |
| `mode` | `"primary"` = main conversation only, `"subagent"` = @mentions only, `"all"` = both |
| `description` | Shown in agent selector UI |

### Step 4: Create a companion skill (optional)

Create `~/.config/opencode/skills/<name>/SKILL.md` with a `trigger` for slash-command discovery. This injects methodology context into the agent when loaded. The research agent uses `trigger: /research`.

### Step 5: Test

```bash
# Smoke test — does the agent load and respond?
opencode run --agent <name> 'Respond with exactly: <NAME>_SMOKE_OK. Do nothing else.'

# Tool test — do MCP tools connect?
opencode run --agent <name> 'Search for "test query" and tell me what tool you used.'

# Full workflow test — does the agent do its job?
opencode run --agent <name> '<real task>'
```

### Step 6: Document in AGENTS.md

Add a section in `~/.config/opencode/AGENTS.md` listing custom agents, their prompt files, and activation commands. Future sessions discover them via session-opening protocol.

### Pitfall: Docker MCP env var propagation

MCP servers running in Docker need **both** the flag in the command array AND the value in the `environment` dict:

```json
// CORRECT — -e VARNAME (no =value) + environment dict
"command": ["docker", "run", "-i", "--rm", "-e", "SEARXNG_URL", "image"],
"environment": {
  "SEARXNG_URL": "http://searxng:8080"
}

// WRONG — inline value leaks into ps aux
"command": ["docker", "run", "-i", "--rm", "-e", "SEARXNG_URL=http://searxng:8080", "image"]

// WRONG — flag missing, env var never reaches container
"command": ["docker", "run", "-i", "--rm", "image"],
"environment": {
  "SEARXNG_URL": "http://searxng:8080"
}
```

The `-e VARNAME` (without `=`) tells Docker to inherit the var from the host process env. OpenCode injects `environment` dict values into the subprocess env, so Docker picks them up. Missing the `-e` flag means the container never sees the variable regardless of the `environment` dict.

## Pitfalls

- **Don't assume tools exist**: Test that the target platform actually has the tool before referencing it. OpenCode's `grep` and `webfetch` are native tools; `execute_code` is not — use `bash` with python3 instead.
- **Frontmatter is stricter in OpenCode**: Only `name`, `description`, and `trigger` are recognized. Extra fields are silently ignored but clutter the file.
- **OpenCode discovers skills by directory**: Each skill must be in its own subdirectory with a `SKILL.md` file. A single `.md` file in the skills root won't be found. **Critical: must be a real directory, NOT a symlink.** OpenCode does not follow symlinks for skill discovery. If copying skills from another agent (e.g., Hermes), use `cp -r`, not `ln -s`.
- **Claude Code shared path is read by both**: Skills at `~/.claude/skills/` are loaded by both Claude Code AND OpenCode. Changes here affect both platforms — be careful with platform-specific instructions.
- **Agent mentions ≠ delegate_task**: OpenCode `@agent` dispatches subagents inline in the conversation. Hermes `delegate_task` spawns isolated subprocesses. The context isolation model is different.
- **Trust dialogs differ**: Hermes prompts for dangerous commands; OpenCode uses permission sets in `opencode.json`. Ported skills shouldn't assume any particular approval flow.
- **System prompt length matters**: OpenCode compacts context near the window limit. Long AGENTS.md files or agent prompts consume tokens better used for conversation. Keep prompts under ~4KB if possible.

## References

- `references/opencode-agent-permissions.md` — Full permission configuration dump from OpenCode v1.15.5, including all 9 agent types and their permission matrices. Useful when diagnosing why a ported skill's tool calls fail on OpenCode.
- `references/opencode-research-agent-prompt.md` — Battle-tested 17-module system prompt for creating a custom internet research agent on OpenCode. Includes structured output format, source quality tiers, verification methodology, and question-asking patterns. Use as a template when building any non-coding custom agent.
- `references/hermes-review-to-opencode-port.md` — Case study: porting Hermes's background review loop (`agent/background_review.py`) to OpenCode using a 3-layer approach (prompt injection + standalone skill + subagent). Documents file locations, config patterns, and verification commands.
- `references/system-spec-opencode-port.md` — Case study: porting a data/reference skill (system HW/SW spec) from Hermes to OpenCode. Shows frontmatter stripping (rich → minimal), tool ref adaptation (`skill_manage` → `edit`), and why spec/reference skills port cleanly with minimal adaptation.
