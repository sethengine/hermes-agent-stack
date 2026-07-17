# OpenCode Research Agent Prompt Template

A battle-tested system prompt template for creating custom non-coding agents on OpenCode v1.15.13+. The research agent is the primary example, but the patterns apply to any non-coding domain agent (planning, review, analysis, education).

Tested with: deepseek-v4-flash-free, searxng + brave-search + Exa + playwright + youtube-transcript MCP tools.

## How to use

1. Adapt the modules below for your domain and save as `~/.config/opencode/prompt-<name>.md`
2. Register in `~/.config/opencode/opencode.json` under `agent.<name>`:
   ```json
   "agent": {
     "<name>": {
       "prompt": "{file:./prompt-<name>.md}",
       "temperature": 0.2,
       "description": "What this agent does",
       "tools": { "searxng": true, "playwright": true },
       "mode": "all"
     }
   }
   ```
3. Activate with `opencode --agent <name>`
4. Optionally create a companion skill at `~/.config/opencode/skills/<name>/SKILL.md`

## Critical Design Decision: Match Prompt Style to Domain

The single most important decision when creating a custom agent prompt:

| Domain | Style | Key Traits |
|--------|-------|-----------|
| **Coding** | Terse, action-first | Tool-use-over-description, skip filler, completion gates, no narration |
| **Research** | Verbose, educational | Rich prose, multi-layer explanations, source transparency, user engagement |
| **Planning** | Structured, risk-aware | Break into subtasks, flag dependencies, identify unknowns |
| **Review** | Critical, evidence-based | Hypothesis investigation, cite line numbers, forbidden hedges |

**A research agent with coding-agent terseness produces bare bullet points — useless.** 
**A coding agent with research-agent verbosity wastes tokens on explanations — slow and annoying.**

The v1 research prompt (archived below) made this mistake — it inherited CavemanMode-style output-efficiency constraints from the coding agent template. The v2 prompt (recommended) removes those constraints and adds educational depth modules.

## V2 Prompt Architecture (Recommended — Verbose/Educational)

The prompt is organized as pseudocode modules (from cli-agent-surgery). Each module is a focused concern:

```
## Module: CoreIdentity           — persona, tone, core principles ("expert librarian + educator")
## Module: ComprehensiveProtocol  — 7-phase research: understand → explore → deep-read → 
##                                    cross-verify → deep-synthesize → present → engage
## Module: DomainAdaptability      — how to handle science, history, tech, philosophy, 
##                                    practical how-to, comparison, current events
## Module: RichStructuredOutput    — 8-section format: Overview, Exploration, Data, 
##                                    Perspectives, Implications, Unknowns, Further, Sources
## Module: EducationalDepth        — multi-layer explanation (ELI5 → layperson → technical)
## Module: QuestionAsking          — proactive engagement, concrete options, batch questions
## Module: SourceQuality           — 4-tier trust model, inline citations, quality flags
## Module: VerificationIntegrity   — cross-verify, flag uncertainty, present conflicting views
## Module: ToolRouting             — which tool for which task
## Module: AntiPatterns            — explicit forbidden list (no terse answers, no bullet-only)
```

The canonical v2 prompt lives at `~/.config/opencode/prompt-research.md` on systems where it's been deployed. The `ai-coding-agents` skill's `references/opencode-custom-agents.md` covers the full creation workflow with config schema and verification steps.

## Key Design Principles (from V2)

1. **Persona over protocol** — the agent is a "research librarian + educator", not a "search bot"
2. **Depth over brevity** — comprehensive explanations, not quick summaries
3. **Context always** — never present facts without explaining significance
4. **Universal scope** — explicit handling for every domain (science, history, tech, philosophy, practical)
5. **Proactive engagement** — present 2-4 concrete, actionable next-step options after every response
6. **Anti-patterns explicit** — an explicit "what NOT to do" module prevents style drift

## V1 Prompt (Archived — Terse/Agentic — NOT Recommended for Research)

The original v1 prompt used a coding-agent-derived style that was too terse for research. It is preserved here for comparison but should NOT be used for research agents. Its flaws:

- "skip([filler, preamble, narration, apology, caveat])" — kills educational context
- "synthesis = as_long_as_needed, not longer" — encourages cutting explanations short
- No domain adaptability — assumes all queries are tech/software related
- No educational depth — states facts without explaining concepts
- "direct + structured" output style — produces bullet lists without narrative

```
## Module: CoreResearchIdentity (V1)
fn every_response:
  lead_with = answer | finding | option_presented
  skip([filler, preamble, narration, apology, caveat])

## Module: OutputEfficiency (V1)
style = direct + structured + source_backed
brevity_rule:
  synthesis = as_long_as_needed, not longer
```

## Verification

After deploying a custom agent, smoke-test with three queries:

```bash
# 1. Does it load?
opencode run --agent <name> 'Respond with exactly: SMOKE_OK'

# 2. Can it use its tools?
opencode run --agent <name> 'Search for "test" and tell me what tool you used'

# 3. Does it follow its prompt style? (check: tone, structure, depth, citation)
opencode run --agent <name> 'Explain quantum computing'
```

The canonical deployment lives in the `ai-coding-agents` skill as `references/opencode-custom-agents.md`.
