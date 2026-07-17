---
name: claude-code
description: Delegate coding tasks to Claude Code CLI (Anthropic's agent) as a subprocess from OpenCode. Features, PR review, refactoring.
---

# Claude Code — Subprocess Orchestration from OpenCode

Delegate coding tasks to [Claude Code](https://code.claude.com/docs/en/cli-reference) (Anthropic's autonomous coding agent CLI) via bash subprocesses.

## Prerequisites

- **Install:** `npm install -g @anthropic-ai/claude-code`
- **Auth:** run `claude` once to log in (browser OAuth for Pro/Max, or set `ANTHROPIC_API_KEY`)
- **Check:** `claude --version` (requires v2.x+)
- **Health:** `claude doctor`

## Two Modes

### Mode 1: Print Mode (`-p`) — PREFERRED for automation

Print mode runs a one-shot task, returns the result, and exits. No interactive prompts.

```bash
claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10
```

**When to use:**
- One-shot coding tasks (fix a bug, add a feature, refactor)
- Scripting and automation
- Any task where you don't need multi-turn conversation

### Mode 2: Interactive Mode — for multi-turn work

```bash
# Start Claude Code interactively in a directory
cd /path/to/project && claude
```

Use for exploratory coding or when you need Claude's slash commands (`/compact`, `/review`, `/model`).

## Key CLI Flags

| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot mode |
| `-c, --continue` | Resume most recent conversation |
| `-r, --resume <id>` | Resume specific session |
| `--model <alias>` | Model: `sonnet`, `opus`, `haiku` |
| `--max-turns <n>` | Limit agentic loops (print mode only) |
| `--max-budget-usd <n>` | Cap API spend |
| `--effort <level>` | Reasoning depth: `low`, `medium`, `high`, `max` |
| `--allowedTools <tools...>` | Whitelist tools (e.g., `Read,Edit`) |
| `--dangerously-skip-permissions` | Auto-approve ALL tool use |
| `--output-format json` | Machine-readable output |
| `--json-schema <schema>` | Force structured JSON output |
| `--bare` | Skip hooks, plugins, MCP discovery (fastest) |

## Common Patterns

### One-shot Fix

```bash
claude -p 'Fix the race condition in src/cache.py and add a test' --allowedTools 'Read,Edit,Write,Bash' --max-turns 10
```

### Code Review (Print Mode)

```bash
cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems.' --max-turns 1
```

### Structured Output

```bash
claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5
```

Returns JSON with `session_id`, `num_turns`, `total_cost_usd`, `result`, and `usage`.

### Piped Input

```bash
# Pipe a file for analysis
cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1

# Pipe git diff for review
git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1
```

### Continue a Session

```bash
# Continue the most recent session in the same directory
claude -p 'Now add integration tests' --continue --max-turns 10

# Resume a specific session by ID
claude -p 'Continue the refactoring' --resume ses_abc123 --max-turns 5
```

## Parallel Work Pattern

```bash
# Launch multiple Claude instances in different worktrees
cd /project && git worktree add -b fix/auth /tmp/fix-auth main
cd /project && git worktree add -b fix/api /tmp/fix-api main

# Run Claude in each (they don't block each other)
cd /tmp/fix-auth && claude -p 'Fix the auth bug in src/auth.py' --allowedTools 'Read,Edit' --max-turns 10
cd /tmp/fix-api && claude -p 'Add rate limiting to API' --allowedTools 'Read,Edit,Write' --max-turns 10
```

## CLAUDE.md — Project Context

Claude Code auto-loads `CLAUDE.md` from the project root. Use it to persist project context:

```markdown
# Project: My API

## Architecture
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database, Redis cache
- pytest for testing with 90% coverage target

## Key Commands
- `make test` — run full test suite
- `make lint` — ruff + mypy
- `make dev` — start dev server on :8000

## Code Standards
- Type hints on all public functions
- 4-space indentation for Python
- No wildcard imports
```

**Be specific.** Instead of "Write good code", use "Use 2-space indentation for JS" or "Name test files with `.test.ts` suffix."

## Slash Commands (Interactive Mode)

| Command | Purpose |
|---------|---------|
| `/review` | Request code review of current changes |
| `/security-review` | Security analysis of changes |
| `/plan` | Enter Plan mode for task planning |
| `/compact` | Compress context to save tokens |
| `/clear` | Wipe conversation history |
| `/cost` | View token usage |
| `/model` | Switch models mid-session |
| `/init` | Create a CLAUDE.md file |
| `/memory` | Open CLAUDE.md for editing |

## Custom Skills

Create `.claude/skills/` directory with markdown guides that Claude invokes automatically via natural language matching:

```markdown
# .claude/skills/database-migration.md
When asked to create or modify database migrations:
1. Use Alembic for migration generation
2. Always create a rollback function
3. Test migrations against a local database copy
```

## Cost & Performance Tips

1. **Use `--max-turns`** — prevent runaway loops. Start with 5-10.
2. **Use `--max-budget-usd`** — cap API spend.
3. **Use `--effort low`** for simple tasks, `high`/`max` for complex reasoning.
4. **Use `--bare`** for CI/scripting — skips plugin/hook overhead.
5. **Use `--allowedTools`** — restrict to only what's needed.
6. **Use `--model haiku`** for simple tasks (cheaper).
7. **Pipe input** instead of having Claude read files when you just need analysis.
8. **Start new sessions for distinct tasks** — fresh context is more efficient.
