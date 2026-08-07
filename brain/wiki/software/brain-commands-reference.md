---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [brain, commands, reference, cli]
---

# Brain Commands Reference

The Global Session Brain provides these commands for interacting with durable knowledge:

| Command | Description | Token Cost |
|---------|-------------|-----------|
| `/brain extract` | Extract knowledge from new/unprocessed sessions. Runs LLM categorization on each session | ~25-40K per new session |
| `/brain query "..."` | Semantic graph lookup — returns relevant subgraph (~200-500 tokens) instead of grep-hunting | ~50 tokens |
| `/brain path "A" "B"` | Find shortest path between two concepts via graph traversal | ~50 tokens |
| `/brain explain "X"` | Show all connections for a given concept node | ~50 tokens |
| `/brain stats` | Show node count, file count, session coverage | ~50 tokens |
| `/brain update` | Rebuild graph from wiki (runs graphify --update) | ~100 tokens idle |

## Automation

- **Cron**: Runs `/brain extract` + `/brain update` every 2 hours
- **Manual**: Any command can be run on-demand

## Query Examples

- `/brain query "GPU audio interference fix"` — retrieves connected nodes about coil whine and PipeWire
- `/brain path "nvidia-xid" "kernel-panic"` — finds causal links between GPU errors and system crashes

See also: [[global-session-brain-architecture]], [[brain-knowledge-extraction-pipeline]], [[graphify-wiki-retrieval]], [[brain-wiki-category-structure]]
