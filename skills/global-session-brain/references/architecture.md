# Global Session Brain — Architecture

## Overview

The Global Session Brain is Hermes' long-term memory system. It extracts durable knowledge from conversation sessions, categorizes it into a structured wiki, builds a knowledge graph over the wiki, and provides sub-500-token graph queries for context-efficient recall.

**Core insight:** Small-context LLMs burn tokens on grep-hunting (guessing file names, reading irrelevant content, re-searching). A graph knows what's connected — one traversal call returns the exact relevant subgraph.

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Hermes Agent Loop                      │
│                                                           │
│  ┌─────────┐    ┌──────────┐    ┌──────────────────────┐ │
│  │ MEMORY  │    │  Skills   │    │  Global Session Brain │ │
│  │ .md     │    │  (SKILLs) │    │  (this skill)         │ │
│  │ ~2K ch. │    │           │    │                       │ │
│  └────▲────┘    └──────────┘    └───────────┬───────────┘ │
│       │                                      │             │
│  System prompt                              │             │
│  (frozen snapshot)                    On-demand query      │
└─────────────────────────────────────────────┼─────────────┘
                                              │
                          ┌───────────────────┼───────────────┐
                          │   Brain Pipeline  │                │
                          │                   ▼                │
                          │  ┌─────────────────────────────┐  │
                          │  │  Session JSON Files           │  │
                          │  │  (~/.hermes/sessions/*.json)  │  │
                          │  └──────────────┬──────────────┘  │
                          │                 │                  │
                          │      /brain extract (LLM)         │
                          │                 │                  │
                          │                 ▼                  │
                          │  ┌─────────────────────────────┐  │
                          │  │  Wiki Directory               │  │
                          │  │  (~/.hermes/brain/wiki/*/)    │  │
                          │  │  Categorized .md files        │  │
                          │  └──────────────┬──────────────┘  │
                          │                 │                  │
                          │        graphify --update          │
                          │                 │                  │
                          │                 ▼                  │
                          │  ┌─────────────────────────────┐  │
                          │  │  Knowledge Graph              │  │
                          │  │  graphify-out/graph.json      │  │
                          │  │  nodes + edges + communities  │  │
                          │  └──────────────┬──────────────┘  │
                          │                 │                  │
                          │   graphify query / path / explain │
                          │                 │                  │
                          │                 ▼                  │
                          │       LLM receives subgraph       │
                          │       (200-500 tokens)            │
                          └──────────────────────────────────┘
```

## Data Flow

### 1. Extraction Phase (`/brain extract`)

**Trigger:** Manual `/brain extract` command or periodic cron job.

**Flow:**
1. `scripts/track_sessions.py --list-new` finds unprocessed session JSONs
2. For each unprocessed session, the LLM reads the session file
3. The LLM extracts **durable knowledge**:
   - System configurations discovered
   - Bug fixes and workarounds
   - Concepts explained or learned
   - Decisions made and their rationale
   - Tools or commands discovered
4. The LLM categorizes each piece of knowledge into a wiki subdirectory
5. Writes a concise markdown file (max 200 words) with metadata header
6. Runs `scripts/track_sessions.py --mark-done SESSION_ID`

### 2. Indexing Phase (graphify)

**Trigger:** After extraction completes, or manual `/brain update`.

**Flow:**
1. graphify's `--update` detects new/changed files in `wiki/`
2. Semantic extraction runs on new markdown files:
   - Concepts extracted as nodes
   - Cross-references, `[[wiki-links]]`, and inferred relationships as edges
   - Community detection clusters related concepts
3. `graph.json` updated with new nodes and edges
4. `GRAPH_REPORT.md` regenerated with updated god nodes, surprises, questions

### 3. Query Phase (`/brain query`)

**Trigger:** LLM needs context from past sessions.

**Flow:**
1. LLM calls `graphify query "question"` on `brain/wiki/graphify-out/graph.json`
2. BFS traversal (depth 3) finds relevant subgraph
3. Subgraph returned: ~200-500 tokens (nodes + edges)
4. LLM synthesizes answer from subgraph
5. Query result saved back to graph via `graphify save-result` (improves future queries)

## File Conventions

### Wiki File Format

Each extracted knowledge file follows this template:

```markdown
---
session: session_20260611_190438_422897
date: 2026-06-11
category: audio
tags: [pipewire, coil-whine, alc1220]
---

# PipeWire ALC1220 Custom Sink Workaround

Concrete statement of the knowledge. Keep under 200 words.

## References
- [[NVIDIA Xid 31 audio interference]]
- [[Kernel C2/C3 state config]]
```

### Category Guidelines

| Category | What goes there |
|----------|----------------|
| `audio/` | PipeWire config, EasyEffects, coil whine, audio hardware |
| `gpu/` | NVIDIA drivers, Xid errors, Wayland compositor, GPU config |
| `kernel/` | Kernel params, IRQ pinning, CPU scheduling, cmdline |
| `system/` | Hardware details, BIOS settings, motherboard quirks |
| `software/` | Apps, dotfiles, Hermes config, development tools |
| `ml/` | ML concepts, model architectures, training, inference |
| `research/` | Papers, findings, investigations, benchmarks |
| `sessions/` | Session-level summaries (auto-extracted) |

New categories can be created as needed.

## Integration Points

### With MEMORY.md / USER.md

The brain does NOT replace the small curated memory. Their roles:

- **MEMORY.md**: "What should the LLM know for EVERY turn?" (preferences, environment, immediate context)
- **Brain**: "What might the LLM need to look up?" (past fixes, complex configs, learned concepts)

When a brain entry becomes frequently accessed, consider promoting a summary to MEMORY.md.

### With Skills System

The brain skill sits alongside other skills. When loaded, it adds `/brain *` commands. It does NOT modify any other skill.

### With research-assistant

The `research-assistant` skill already references graphify for wiki retrieval. The brain extends this pattern to session-derived knowledge:

```
research-assistant  →  graphify over user-curated wiki
global-session-brain →  graphify over auto-extracted session wiki
```

Both skills can coexist. An LLM should prefer:
1. MEMORY.md → if the fact is there, use it (free, always loaded)
2. Brain query → if the fact might be in past sessions
3. research-assistant wiki → if the fact might be in curated research

### With graphify

The brain is a consumer of graphify. It uses:
- `graphify --update` for incremental re-indexing
- `graphify query` for BFS/DFS retrieval
- `graphify path` for concept-to-concept navigation
- `graphify explain` for node detail

It does NOT run the full graphify pipeline (Steps 1-9 from the graphify skill) — that's for initial builds or full rebuilds.

## Token Economics

### Cost of extraction (paid once per session)

Extracting a typical 50-message session:
- Reading session JSON: ~8K tokens
- LLM extraction reasoning: ~2K tokens
- Writing 3-5 wiki files: ~1K tokens
- **Total per session: ~11K tokens** (one-time cost)

### Savings per query (paid every lookup)

| Scenario | Without brain | With brain | Saved |
|----------|-------------|-----------|-------|
| Simple lookup ("what was that fix") | 1K–3K | 200–400 | 60-90% |
| Multi-hop query | 3K–8K | 300–600 | 80-95% |
| Cross-session concept | 5K–15K+ | 400–800 | 85-97% |

**Break-even:** After ~2-3 queries on the same knowledge, the brain pays for itself.

## Cron Automation

A Hermes cron job runs extraction every 2 hours:

```
schedule: 0 */2 * * *
skill: global-session-brain
prompt: /brain extract --since 2h
```

This keeps the brain fresh without per-turn overhead. Sessions are processed within ~2 hours of completion.

## Security & Privacy

- All data stays local in `~/.hermes/brain/`
- Session extraction is LLM-driven — the LLM decides what's durable vs transient
- No external APIs called (graphify runs locally)
- `.brain_manifest.json` tracks which sessions have been processed
- Extraction is additive only — never deletes content from the wiki
