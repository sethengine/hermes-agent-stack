---
name: deep-research
description: Multi-pass structured research. Plan → Search → Extract → Verify → Synthesize. Uses web_search, news_search, scholar_search, web_extract. Zero API keys.
version: "1.0"
---

# Deep Research Protocol

## Core Principle

Never report a claim from a single source as fact. Cross-verify across 2+ independent sources.

## Automated Research (research_plan tool)

The `mcp-search-bridge` v4+ provides a `research_plan` tool that automates Passes 1-3 of the manual protocol. It derives sub-queries from the research question (comparison → per-entity + head-to-head; recommendation → reviews + news + specs; how-to → tutorials + troubleshooting; general → overview + news + academic), searches each with context-appropriate categories, cross-deduplicates across all results with fuzzy title matching, and returns a structured synthesis with confidence scores. Use it as a first pass, then manually web_extract the top findings for Pass 4 (verification).

Usage: `research_plan("your question", depth="standard")`
Depths: quick (2 sub-queries), standard (3-4), deep (5-6).

**SearXNG tuning prerequisite:** the default SearXNG `request_timeout: 3.0` causes empty results for deep queries. See `mcp-search-bridge` skill for the full tuning sed one-liner (6s timeout, 50 pool, shorter bans). Without this, research_plan sub-queries return thin/no results.

### Pass 1: PLAN
Before searching, write:
```
QUESTION: [one sentence]
SUB-QUESTIONS: 1. 2. 3.
SOURCES: [types to prioritize]
VERIFICATION: [cross-check strategy]
```

### Pass 2: SEARCH (breadth)
- web_search for each sub-question, vary phrasing
- news_search for current topics
- scholar_search for academic angle
Collect top 5-10 URLs per search.

### Pass 3: EXTRACT (depth)
web_extract the most promising URLs. Read full content — not just snippets. Prefer docs over blogs, primary over secondary, recent over stale.

### Pass 4: VERIFY
- Same fact in 2+ independent sources?
- Any contradictions? Surface them, don't smooth over.
- Numbers consistent across sources?
- Source authoritative on this topic?

### Pass 5: SYNTHESIZE
For each key insight:
```
FINDING: [one sentence]
EVIDENCE: [direct quote or data]
SOURCE: [name](URL)
CONFIDENCE: high | medium | low
  high = 3+ independent primary sources agree
  medium = 2 sources or 1 primary
  low = single secondary, or conflicting
GAPS: [what's still unknown]
```

## Fallback Search Strategy (when primary tools are unavailable)

The `web_search` / `web_extract` / `news_search` / `scholar_search` tools (Firecrawl-based) may not be configured. When they fail, use this layered fallback stack — try in order, stop when you get usable results:

1. **SearXNG MCP bridge** (`mcp__searxng__web_search`, `mcp__searxng__web_extract`, `mcp__searxng__news_search`, `mcp__searxng__scholar_search`, `mcp__searxng__research_plan`) — free, no API key. Multi-engine federated search (SearXNG → DDG → Wikipedia → arXiv) with fuzzy dedup and category-aware ranking. Also supports structured multi-query research plans. Searches are cached (5min TTL) for instant repeat queries.

2. **Crawl4AI MCP** (`mcp__c4ai__md`) — best for retrieving full page content from any URL. Returns clean markdown. Use `f=raw` for full page, `f=bm25` with `q` param for targeted extraction. Most reliable single-page fetcher.

3. **Playwright browser** (`mcp__playwright__browser_navigate` + `mcp__playwright__browser_snapshot`) — navigates real pages. Use when 1-2 fail for a specific URL. Navigate first, then snapshot.

4. **SearXNG web extract** (`mcp__searxng__web_extract`) — fetch a known URL's content directly (bypass the search step). Good for extracting docs from URLs found via other means.

**Document search tool failures as a GAP in the final synthesis.** Do not silently skip sources. Report which tools failed so the user knows what wasn't verified. This honesty builds trust and helps debug tool configuration.

## Source Quality

Prefer: primary sources > practitioner testimony > aggregator analysis > single-author blogs

Red flags: no date, no author, "studies show" without citation, affiliate-link-heavy

## Anti-Patterns

- Claim from search snippet = fact ❌
- Skip extraction, cite blindly ❌
- Hide contradictions ❌
- Cite unread sources ❌
- Treat LLM training data as source ❌
- Use likes/upvotes as truth signal ❌

## Quick Mode

Skip Pass 3. Flag all findings CONFIDENCE: medium. Note: "Quick mode — not verified against full source text."
