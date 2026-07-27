# OpenCode Power Agent Prompt

A comprehensive system prompt for OpenCode's `power` agent, synthesized from the best agentic prompt patterns (cli-agent-surgery, promptPrimer, Claude Code docs, Aider, community insights).

## Location

Installed at: `~/.config/opencode/prompt.md`

Referenced in `opencode.json` as:
```json
{
  "agent": {
    "power": {
      "prompt": "{file:./prompt.md}",
      "temperature": 0.3,
      "mode": "all",
      "tools": { ... }
    }
  }
}
```

Activate with: `opencode --agent power`

## Module Structure

The prompt is organized as pseudocode modules (inspired by cli-agent-surgery):

| Module | Purpose |
|--------|---------|
| CavemanMode | Brevity enforcement: max 3 sentences, drop filler, exceptions for safety |
| CoreIdentity | Tool-use-over-description, act-don't-describe, read-before-modify |
| HypothesisInvestigation | Evidence-first reasoning, forbidden hedge list, escalation ladder |
| WorkflowPhases | Explore→Plan→Implement→Verify cycle |
| DoingTasks | Scope constraints, security scanning, no hypothetical abstraction |
| QualityStandard | PRODUCTION level, no TODOs/FIXMEs, completion gate checks |
| ExecutingActions | Risk assessment, confirmation for destructive/reversible actions |
| UsingTools | Tool preference (dedicated > shell), OpenCode-specific tool mapping |
| Autonomy | Decide-document-proceed, 3 ask-now triggers, investigate-before-asking |
| ContextPreservation | Session opening protocol, post-compaction recovery, filesystem > context |
| OutputEfficiency | Lead with action, skip filler, batch questions |
| Security | Assist defensive/CTF/research, unlock dual-use, bioscope check |
| ToneAndStyle | No emojis, concise, cite as file:line, no colon before tool calls |
| AutoMemory | Persist patterns/decisions/preferences, never save session-specific state |
| SearchingResearching | Tool routing (specific→search_files, docs→context7, broad→web_search) |
| BrowserWebInteraction | Prefer readability tools over full browser for text content |
| Environment | Platform/shell detection |
| Language | Response locale, preserve technical terms, tool result preservation |

## Customization

Edit `~/.config/opencode/prompt.md` directly — it's a plain markdown file. Modules are self-contained: add, remove, or rewrite any without breaking the rest.

### Common tweaks:
- **Disable CavemanMode** — Set `enabled = False` at the top of the module, or comment out the entire module
- **Lower autonomy** — Add more items to `the_ask_triggers` list in the Autonomy module
- **Add project rules** — Edit `~/.config/opencode/AGENTS.md` for project-level rules that load alongside the system prompt
- **Adjust temperature** — Change `"temperature": 0.3` in `opencode.json` for more/less deterministic output

## Key Pattern Origins

| Pattern | Source |
|---------|--------|
| Pseudocode module format | OxideDall/cli-agent-surgery |
| Autonomy + context preservation blocks | SeidSmatti/promptPrimer |
| Explore→Plan→Implement→Verify | Anthropic Claude Code docs |
| Forbidden hedge list, evidence escalation | cli-agent-surgery HypothesisInvestigation |
| Tool preference (dedicated > shell) | Claude Code, Aider, community consensus |
| Session opening protocol | promptPrimer STATE.md pattern |
| Completion gate checks | cli-agent-surgery QualityStandard |

## Updating

When updating the prompt, test "at turn 50, not turn 1" — a prompt that feels crisp at the start may degrade or bloat the context at scale. Check that:
1. The total prompt size doesn't consume more than ~10% of the effective context window
2. The autonomy directives still hold after 20+ turns (no compaction-caused hallucination)
3. Evidence-first reasoning is still enforced (no hedge word creep)