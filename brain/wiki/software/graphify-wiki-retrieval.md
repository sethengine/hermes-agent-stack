---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [graphify, wiki, retrieval, knowledge-graph]
---

# Graphify Wiki Retrieval

Graphify converts the brain wiki into a knowledge graph for semantic lookup, replacing grep-based file search.

## How It Works

1. **Index** — `graphify` reads all markdown files in `~/.hermes/brain/wiki/` and extracts entities and relationships using LLM analysis
2. **Incremental** — `graphify --update` only re-processes changed files, making repeated runs cheap
3. **Query** — `graphify query "topic" --budget 500` returns the most relevant subgraph (~200-500 tokens)
4. **Output** — A `graph.json` with nodes, edges, and community clusters (19 communities from initial build)

## Why Graph Over Vector DB

| Factor | Graph (graphify) | Vector DB |
|--------|-----------------|-----------|
| Infrastructure | Zero (files only) | Requires running service |
| Query cost | ~200-500 tokens | Embedding + retrieval |
| Misses | LLM-driven relevance | Similarity threshold misses |
| Relationships | Explicit edges | Implicit (embedding proximity) |

## Commands

- `graphify --update ~/.hermes/brain/wiki/` — Incremental re-index
- `graphify query "multi-hop relationship" --budget 500` — Semantic lookup

See also: [[global-session-brain-architecture]], [[brain-knowledge-extraction-pipeline]], [[brain-commands-reference]], [[hermes-memory-systems-overview]]
