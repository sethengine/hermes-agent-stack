---
name: ai-coding-agents
description: "Delegate coding tasks to autonomous AI agent CLIs: Claude Code, OpenAI Codex, and OpenCode."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Delegation, Automation, PR, Refactoring]
---

# AI Coding Agent Delegation

Use external autonomous coding agents as implementation lanes while Hermes retains ownership of task lifecycle, reconciliation, testing, and handoff.

---

## Claude Code (Anthropic)

Install: `npm install -g @anthropic-ai/claude-code`
Auth: `claude auth login` (browser OAuth) or `ANTHROPIC_API_KEY`
Check: `claude auth status`, `claude doctor`

### When to use
- Feature implementation, refactoring, PR reviews
- Batch issue fixing
- Long-running coding sessions with progress checks

### Key commands
```bash
claude --version
claude auth login --console    # API key billing
claude auth login --sso        # Enterprise
claude doctor                  # Health check
```

### Orchestration from Hermes
```bash
# One-shot
terminal(command="claude -p 'Implement user authentication using JWT tokens'", timeout=300)

# PTY interactive (use tmux)
terminal(command="tmux new-session -d -s claude 'claude'", timeout=10)
terminal(command="tmux send-keys -t claude 'Implement auth service' Enter", timeout=5)
terminal(command="tmux capture-pane -t claude -p", timeout=5)
```

---

## OpenAI Codex

Install: `npm install -g @openai/codex`
Auth: `OPENAI_API_KEY` or Codex OAuth
Check: `codex --version`

### Key requirements
- Must run inside a git repository
- Use `pty=true` for interactive sessions
- Hermes-managed OAuth lives in `~/.hermes/auth.json` after `hermes auth add openai-codex`

### Orchestration from Hermes
```bash
# One-shot
terminal(command="codex 'Add pagination to the user list endpoint'", timeout=300)

# Review mode
terminal(command="codex review", timeout=300)
```

---

## OpenCode

Install: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
Auth: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
Check: `opencode auth list`

### When to use
- Provider-agnostic agent (works with OpenRouter, Anthropic, DeepSeek, etc.)
- Long-running sessions with progress checks
- Parallel task execution in isolated workdirs
- **Custom agents** for non-coding domains (research, planning, review)

### Orchestration from Hermes
```bash
# One-shot
terminal(command="opencode run 'Implement OAuth2 login flow'", timeout=300)

# One-shot with custom agent
terminal(command="opencode run --agent research 'Explain CRISPR gene editing'", timeout=300)

# Interactive via tmux
terminal(command="tmux new-session -d -s opencode 'opencode'", timeout=10)
```

### Custom Agents

OpenCode supports custom agents beyond the built-in `build`/`plan`/`general`/`simple`. Each gets its own system prompt, tool permissions, model, and temperature — defined in `~/.config/opencode/opencode.json` under the `agent` key.

**Critical design rule**: Match prompt style to domain. Coding agents need terseness and action-focus (CavemanMode). Research agents need verbosity, educational depth, and user engagement. A research agent with coding-agent terseness produces bare bullet points — useless. See `references/opencode-custom-agents.md` for the full guide.

**Example: Research agent** (`opencode --agent research`):
```
{file:./prompt-research.md}  →  system prompt (expert librarian + educator persona)
temperature: 0.2              →  deterministic, factual
mode: "all"                   →  available as primary + subagent
tools: searxng, brave-search, youtube-transcript, playwright, context7, c4ai, crawl, github
```

### MCP Server Configuration

Docker-based MCP servers need `-e VARNAME` in the command array AND the value in the `environment` dict. Without the `-e` flag, Docker doesn't inherit the var and the container sees it as unset. See `references/opencode-mcp-servers.md` for full networking patterns, env var pitfalls, and per-image config.

### Terminal Integration (Clickable Links)

OpenCode renders links with ANSI styling only — no OSC 8 hyperlink sequences. Links look clickable but aren't. Fix at the terminal level with Alacritty hints (regex-based URL detection + wrapper script). **Note**: OpenCode TUI enables mouse reporting, which blocks Ctrl+Click. Use keyboard hint mode (`Ctrl+Shift+U`) instead — it always works regardless of application mouse mode. See `references/opencode-terminal-integration.md` for the complete config including common regex pitfalls (`\b`, `action = "Open"`).

### Reference Files

| File | Contents |
|------|----------|
| `references/opencode-mcp-servers.md` | MCP server config, Docker networking, SearXNG JSON format, env var pitfalls |
| `references/opencode-prompt-architecture.md` | Prompt assembly flow, provider-specific prompts, subagent prompts, agent schema |
| `references/opencode-power-agent-prompt.md` | Power agent prompt breakdown (module structure, customization, pattern origins) |
| `references/opencode-custom-agents.md` | Custom agent creation: prompt design by domain, config schema, verification |
| `references/opencode-terminal-integration.md` | Alacritty hints config for clickable links, wrapper script, markdown URL regex |

---

## Hermes Retains Ownership

When delegating to any coding agent:
1. **Start** the agent in an isolated workspace or worktree.
2. **Monitor** progress via tmux capture or log tailing.
3. **Reconcile** diffs back to the main workspace.
4. **Verify** with tests before considering the task done.
5. **Handoff** cleanly — agent output is not a completion signal.
