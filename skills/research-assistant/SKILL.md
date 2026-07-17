---
name: research-assistant
description: "Research and information gathering tools: arXiv papers, blog feeds, LLM wiki, and prediction markets."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, arXiv, Papers, Blogs, Wiki, Prediction-Markets, Information-Gathering]
    related_skills: [graphify, global-session-brain]
---

# Research Assistant

Gather, summarize, and synthesize information from academic papers, blogs, community wikis, and prediction markets.

---

## arXiv Papers

Search, fetch, and summarize academic papers from arXiv.

### Search
```bash
python3 scripts/search_arxiv.py "transformer architecture" --max 10
python3 scripts/search_arxiv.py "GRPO reinforcement learning" --category cs.LG --days 30
```

### Fetch & Summarize
```bash
# Download PDF and extract text
pip install arxiv pymupdf
python3 -c "import arxiv; paper = next(arxiv.Client().results(arxiv.Search(id_list=['2401.12345']))); paper.download_pdf(filename='paper.pdf')"
```

---

## Blog & Feed Monitoring

Track blog posts and RSS/Atom feeds via the `blogwatcher-cli` tool.

### Setup
```bash
pip install blogwatcher
blogwatcher add "https://example.com/feed.xml" --name "Example Blog"
```

### Query
```bash
blogwatcher list
blogwatcher fetch --since "2 days ago"
blogwatcher search "LLM training"
```

---

## LLM Wiki

Build and query an interlinked markdown knowledge base about LLMs.

### Workflow
1. Create markdown notes in a dedicated directory.
2. Link between notes using `[[wiki-links]]`.
3. Query via text search or structured retrieval.

### Commands
```bash
# Add a concept note
write_file(path="llm-wiki/attention-mechanism.md", content="...")

# Search the wiki
search_files("attention", path="llm-wiki/")
```

### Structured Retrieval (graphify)

When the wiki grows beyond ~20 files, plain `search_files` (keyword grep) wastes context budget — every wrong guess costs a `read_file` + tool call, and the LLM spends reasoning tokens on hunting instead of answering.

[graphify](/graphify) can serve as a **structured retrieval layer** over the wiki:

```bash
# One-time build: index the wiki as a knowledge graph
/graphify llm-wiki/ --mode deep

# Then query via traversal instead of grep
/graphify query "How does attention relate to KV cache?"
/graphify path "Attention" "KV Cache"     # shortest path between concepts
/graphify explain "GroupedQueryAttention"  # node + all edges
```

Each `query` call returns a 200–500 token subgraph (BFS depth-3) — the LLM reads only what's relevant, zero wasted context.

See `references/retrieval-strategies.md` for detailed tradeoffs between grep, vector DB, and graph traversal.

---

## Prediction Markets (Polymarket)

Query Polymarket for market prices, order books, and historical data.

### Setup
```bash
pip install polymarket-py
```

### API Endpoints
See `references/polymarket-api-endpoints.md` for endpoint details.

### Script
```bash
python3 scripts/polymarket.py --market "Will it rain tomorrow" --history
```

---

## Retrieval Strategy & Context Budget

**Core insight:** Every wrong file guess burns 500–5K tokens on irrelevant reads, then the LLM re-guesses. On a 32K context model, 2-3 misses cost 10% of your budget before any reasoning happens. Precise retrieval isn't about scale — it's about **preserving context for reasoning**.

| Method | Tokens per lookup | Best for |
|--------|------------------|----------|
| `search_files` (keyword grep) | 1K–10K+ (multiple re-reads) | Small wikis (<20 files), known exact terms |
| `graphify` graph traversal | 200–500 (subgraph) | Semantic lookups, multi-hop relationships |
| `global-session-brain` graph | 200–500 (subgraph) | Auto-extracted session knowledge, cross-session concepts |
| Vector DB (if wired) | ~1K (3-5 chunks) | Fuzzy similarity, "I don't know the exact term" |

**Rules of thumb:**
- ≤20 wiki files → grep is fine, context cost is negligible
- 20–100 files → switch to graphify as the lookup layer
- Session-derived knowledge → use `global-session-brain` (`/brain query`) — it auto-extracts from past conversations
- 100+ files → consider a vector DB or full GraphRAG setup
- Always estimate: 1 lookup = grep cost + read_file cost + re-reading if wrong. Graph/vector trades the "if wrong" term for a small guaranteed cost.

## Synthesis Tips

- Start with arXiv for rigorous, peer-reviewed claims.
- Use blogs for recent developments (6–12 month lag on papers).
- Cross-check Polymarket for real-world probability estimates.
- Maintain an LLM wiki for persistent, queryable knowledge.
