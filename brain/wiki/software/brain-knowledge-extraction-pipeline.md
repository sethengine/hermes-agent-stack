---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [brain, extraction, pipeline, cron]
---

# Brain Knowledge Extraction Pipeline

The pipeline extracts durable knowledge from session conversations and stores it in the brain wiki.

## How It Works

1. **Trigger** — Runs via cron every 2 hours, or on-demand via `/brain extract`
2. **Session scan** — Reads session JSONs from `~/.hermes/sessions/`, tracks which have been processed using a manifest file
3. **LLM extraction** — For each new session, an LLM reads the conversation and extracts:
   - Key concepts and definitions
   - Decisions and reasoning
   - Commands and workflows discovered
   - Links to related concepts
4. **Categorization** — LLM assigns a category (audio, gpu, kernel, ml, research, software, system) and writes a markdown file
5. **Graph update** — After extraction, `graphify --update` incrementally rebuilds the knowledge graph

## Token Cost

- Per new session: ~25-40K tokens for extraction
- Idle runs (no new sessions): ~100 tokens
- Graph query: ~200-500 tokens per lookup (vs 1K-10K+ for grep-hunting)

See also: [[global-session-brain-architecture]], [[brain-commands-reference]], [[brain-wiki-category-structure]], [[graphify-wiki-retrieval]]
