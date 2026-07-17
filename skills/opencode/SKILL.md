---
name: opencode
description: OpenCode CLI reference — commands, agents, providers, sessions, and configuration.
---

# OpenCode CLI Reference

OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.
Version: 1.15.5

## Commands

### Core

| Command | Purpose |
|---------|---------|
| `opencode [project]` | Start TUI in a directory |
| `opencode run [message]` | One-shot execution, exits when done |
| `opencode -c, --continue` | Continue last session |
| `opencode -s, --session <id>` | Resume specific session |
| `opencode --fork` | Fork session when continuing |
| `opencode --agent <name>` | Choose agent (build, plan, etc.) |
| `opencode -m, --model provider/model` | Force specific model |
| `opencode --prompt <text>` | Initial prompt |
| `opencode --pure` | Run without external plugins |

### Session Management

| Command | Purpose |
|---------|---------|
| `opencode session` | Manage sessions |
| `opencode export [sessionID]` | Export session as JSON |
| `opencode import <file>` | Import session from JSON/URL |

### Providers & Models

| Command | Purpose |
|---------|---------|
| `opencode providers` | Manage AI providers and credentials (alias: `opencode auth`) |
| `opencode models [provider]` | List available models |

### Agents

| Command | Purpose |
|---------|---------|
| `opencode agent create` | Create a new agent |
| `opencode agent list` | List all available agents |

### MCP Servers

| Command | Purpose |
|---------|---------|
| `opencode mcp` | Manage MCP servers |

### Stats & Debugging

| Command | Purpose |
|---------|---------|
| `opencode stats` | Show token usage and cost statistics |
| `opencode debug` | Debugging and troubleshooting tools |

### GitHub

| Command | Purpose |
|---------|---------|
| `opencode github` | Manage GitHub agent |
| `opencode pr <number>` | Checkout a GitHub PR branch and run OpenCode |

### Server Modes

| Command | Purpose |
|---------|---------|
| `opencode serve` | Start headless server |
| `opencode web` | Start server + web interface |
| `opencode attach <url>` | Attach to running server |
| `opencode acp` | Start ACP (Agent Client Protocol) server |

### Plugins & Maintenance

| Command | Purpose |
|---------|---------|
| `opencode plugin <module>` | Install plugin (alias: `opencode plug`) |
| `opencode db` | Database tools |
| `opencode upgrade [target]` | Upgrade OpenCode |
| `opencode uninstall` | Uninstall OpenCode |
| `opencode completion` | Generate shell completion |

## Key Options

| Flag | Effect |
|------|--------|
| `--print-logs` | Print logs to stderr |
| `--log-level DEBUG|INFO|WARN|ERROR` | Set log level |
| `--pure` | Run without external plugins |
| `--port <n>` | Port to listen on (default 0) |
| `--hostname <host>` | Hostname to listen on (default 127.0.0.1) |
| `--mdns` | Enable mDNS service discovery |
| `--cors <domains>` | Additional CORS domains |

## One-Shot (`opencode run`)

```bash
# Basic one-shot task
opencode run 'Add retry logic to API calls and update tests'

# With specific model
opencode run 'Refactor auth module' --model openrouter/anthropic/claude-sonnet-4

# Attach context files
opencode run 'Review this config for security issues' -f config.yaml -f .env.example

# Show model thinking
opencode run 'Debug why tests fail in CI' --thinking

# Choose agent
opencode run 'Plan the feature' --agent plan
```

## Interactive TUI

Start the TUI:

```bash
opencode                    # Current directory
opencode /path/to/project   # Specific project
opencode -c                 # Continue last session
```

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

## Session & Cost Management

```bash
# List past sessions
opencode session

# Check token usage
opencode stats
opencode stats --days 7 --models anthropic/claude-sonnet-4

# Export session
opencode export ses_abc123 > session.json
```

## Skills System

OpenCode discovers skills from markdown files in:
- `~/.config/opencode/skills/<name>/SKILL.md` — user-level skills
- `~/.claude/skills/<name>/SKILL.md` — Claude Code shared skills
- Project `.opencode/` directory — project-level config

### Skill Format

```yaml
---
name: skill-name
description: What this skill does and when to use it
trigger: /slash-command    # optional slash command
---

# Skill Content

Markdown instructions here...
```

### Agent Format

OpenCode agents have permission sets defined in `opencode.json`. Agents include:
- `build` — Code implementation with full tool access
- `plan` — Planning mode (edit restricted to plan files)
- `explore` — Read-only code exploration (subagent)
- `general` — General-purpose with broad access
- `power` — Full access but restricted search
- `simple` — Minimal toolset

## Common Patterns

### One-Shot Code Changes

```bash
opencode run 'Add error handling to all API endpoints in src/routes/' --agent build
```

### PR Review

```bash
opencode pr 42    # Fetch PR and start reviewing
```

### Parallel Work

Use separate worktrees or directories for parallel OpenCode instances.

## Paths

- Config: `~/.config/opencode/opencode.json`
- Binary: `~/.opencode/bin/opencode`
- Memory: `~/.opencode/memory/`
- Skills: `~/.config/opencode/skills/`
- Claude shared: `~/.claude/skills/`

## Pitfalls

- `/exit` is NOT a valid OpenCode command — use `Ctrl+C` to exit the TUI
- `Enter` may need to be pressed twice in the TUI
- PATH mismatch can select wrong binary/model config
- Avoid sharing one working directory across parallel OpenCode sessions
