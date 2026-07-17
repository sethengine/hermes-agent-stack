# Retrieval Strategies for LLM Knowledge Bases

## The Context-Budget Problem

A typical wrong-guess lookup sequence:

```
Turn 1: search_files("attention") → 5 results → picks one
Turn 2: read_file(attention-is-all-you-need.md) → 1,200 tokens → 30% relevant
Turn 3: search_files("self-attention") → 3 results → read_file(...) → 800 tokens
Turn 4: now answers — but 2K+ tokens burned on hunting
```

That's ~15% of a 32K context window before any reasoning. Every retrieval method trades token overhead for precision.

## Comparison

| Method | Token cost | Precision | Infrastructure | Latency |
|--------|-----------|-----------|----------------|---------|
| `search_files` (grep) | Low per call, high total | Exact keyword only | None | Instant |
| `graphify` graph traversal | 200–500 (subgraph) | Semantic + relational | One-time build | Fast |
| Vector DB (Chroma/Qdrant) | ~1K (3-5 chunks) | Semantic similarity | Running service + embeddings | Medium |
| Graph DB (Neo4j) | ~200 (query only) | Relational traversal | Running service + maintenance | Medium |

## When to use graphify as a retrieval layer

graphify is the lowest-overhead structured retrieval option because:

1. **One-time cost** — build the graph once, query forever. No per-write embeddings.
2. **Small queries** — BFS depth-3 returns 50–200 nodes, ~200–500 tokens. Compare to reading a full file.
3. **Three query modes** — BFS (broad context), DFS (trace specific path), shortest_path (find connections).
4. **No infra** — runs via the graphify python package, same as any terminal command.

Tradeoff: graphify misses things a vector DB would catch ("self-attention" and "scaled dot-product attention" are separate nodes until the next `--update` re-extracts them). But at wiki scale (<200 files), the misses are rare enough that the infra savings win.

## When to consider a vector DB

- Fuzzy retrieval needs ("something about attention but I don't know the exact term")
- 100+ files where manual curation lags
- You're already running embeddings for another purpose

## When graph DB adds real value over graphify

- Dynamic edges that change per query
- Multi-user write access
- Real-time relationship updates
- Already running Neo4j for another purpose

For the typical wiki use case (10–200 curated markdown files), graphify's one-shot build + traversal queries are the sweet spot.
