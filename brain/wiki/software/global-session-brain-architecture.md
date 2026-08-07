---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [brain, architecture, memory, graphify]
---

# Global Session Brain Architecture

The **Global Session Brain** is Hermes' durable knowledge system. It converts session conversations into a structured, queryable knowledge base.

## Flow

```
Sessions (conversation history)
    ↓  cron: extract knowledge every 2h
LLM extracts durable facts → categorizes
    ↓
Wiki (markdown files by category)
    ↓  graphify --update
Graph (nodes + edges + communities)
    ↓  graphify query
LLM receives ~200-500 token subgraph
```

## Design Principles

- **Sessions → Wiki → Graph** — sessions are ephemeral; wiki files are durable; the graph enables semantic traversal
- **On-demand retrieval** — brain is NOT injected into every system prompt (unlike MEMORY.md). Queried only when relevant
- **Incremental updates** — graphify `--update` only re-processes changed files
- **Coexists with existing memory** — MEMORY.md (always loaded), skills (loaded on trigger), brain (queried on demand)

See also: [[brain-knowledge-extraction-pipeline]], [[brain-commands-reference]], [[brain-wiki-category-structure]], [[hermes-memory-systems-overview]], [[graphify-wiki-retrieval]]
