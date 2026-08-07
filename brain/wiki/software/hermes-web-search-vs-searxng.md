---
source_session: "20260714_223541_c680b2"
extracted_at: "2026-07-15T00:10:00+03:00"
category: software
tags: [hermes, search, searxng, mcp, tools]
---

# Hermes `web_search` vs `mcp__searxng__web_search` Tool Comparison

Hermes provides two search tools with different capabilities:

**`web_search` (built-in):** Simple single-backend search. Has `limit` parameter (1–100) and supports backend-dependent search operators (site:, filetype:). No pagination, no categories, no time range filtering, no language/region support.

**`mcp__searxng__web_search`:** Multi-engine aggregator with significantly more parameters:
- `pageno` — Page through results beyond the first page
- `categories` — 10+ categories: general, news, images, videos, science, files, it, social media, music, map
- `time_range` — Filter by recency (day, week, month, year)
- `language` — Locale-specific results
- `context` — Domain bias (general, tech, news, scholar)
- Fuzzy deduplication — Merges near-identical results from different engines
- Fallback chain — SearXNG primary → DuckDuckGo → Wikipedia + arXiv
- Caching with TTL — Repeated queries return cached results within expiry

When `web_search` has no API-based provider configured, Hermes automatically falls back to `mcp__searxng__web_search`.

Related: [[hermes-mcp-search-tools-improvement]], [[searxng-document]], [[hermes-mcp-profile-configuration]], [[hermes-firecrawl-disable-config]]
