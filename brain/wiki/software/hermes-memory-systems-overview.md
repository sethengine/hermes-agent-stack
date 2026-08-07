---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [memory, brain, skills, session-search]
---

# Hermes Memory Systems Overview

Hermes has multiple memory systems, each serving a different purpose.

| System | Storage | In System Prompt? | Size | Purpose |
|--------|---------|-------------------|------|---------|
| **MEMORY.md** | `~/.hermes/memories/MEMORY.md` | ✅ Every turn | ~2.2K chars | Agent-curated quick facts |
| **USER.md** | `~/.hermes/memories/USER.md` | ✅ Every turn | ~1.1K chars | User profile, preferences |
| **Skills** | `~/.hermes/skills/*/SKILL.md` | ✅ When loaded | Varies | Procedural memory, workflows |
| **Brain Wiki** | `~/.hermes/brain/wiki/` | ❌ On demand | 13+ files | Durable session knowledge |
| **Graph** | `~/.hermes/brain/graphify-out/` | ❌ Query only | 77+ nodes | Semantic traversal |
| **session_search** | `~/.hermes/state.db` (FTS5) | ❌ Search only | Full history | Full-text conversation recall |

## Key Insight

Unlike a vector DB, the brain uses **graph-based retrieval** via graphify. This avoids embedding costs, running a vector service, and probabilistic misses. The graph query returns only the relevant subgraph (~200-500 tokens), preserving context for reasoning.

See also: [[global-session-brain-architecture]], [[graphify-wiki-retrieval]], [[brain-knowledge-extraction-pipeline]]
