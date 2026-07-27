# Running last30days on Hermes

## What It Is

[last30days](https://github.com/mvanhorn/last30days-skill) is a structured multi-platform social-media research engine. Given a topic, it fans out parallel searches across Reddit, X, YouTube, Hacker News, TikTok, Instagram, Polymarket, GitHub, and Bluesky — then clusters findings into narrative themes (Ranked Evidence Clusters) and produces an emoji-tree stats footer. It fills the social-sentiment gap that general web search methodology misses.

## When to Use Instead of General Web Search

| Situation | Use | Why |
|-----------|-----|-----|
| Community sentiment / what people are saying | `last30days` | Multi-platform social corpus, not blogs/news |
| Product/vs comparison research | `last30days` | Real user opinions, not marketing |
| Trend / zeitgeist check | `last30days` | Engagement signals (upvotes, likes, points) |
| Breaking news reaction | `last30days` | Reddit + HN comment threads are faster than journalism |
| Factual/technical question | web search | last30days has no documentation authority |
| API docs / config / setup problem | web search | last30days doesn't index docs |

## Integration Pattern: Hermes

### Prerequisites

```bash
SKILL_DIR="/home/sethengine/.hermes/skills/last30days"
LAST30DAYS_MEMORY_DIR="$HOME/Documents/Last30Days"
mkdir -p "$LAST30DAYS_MEMORY_DIR"

# Python 3.12+ required
LAST30DAYS_PYTHON="python3.14"   # or python3.12 / python3.13
```

### Step 0.55 (Pre-Research) — Use SearXNG

The skill's Step 0.55 wants WebSearch to resolve handles/subreddits. On Hermes, use the SearXNG MCP bridge instead of `web_search` (Firecrawl):

```python
# Resolve subreddits
from hermes_tools import mcp__searxng__web_search
result = mcp__searxng__web_search(query="{topic} subreddit reddit community")

# Resolve news/current events context
result = mcp__searxng__web_search(query="{topic} news {MONTH} {YEAR}")
```

**SearXNG limitations on Hermes:**
- Best for subreddit discovery, news context, and Wikipedia-style overviews
- Weak on practical/self-help topics (returns academic papers instead of community content)
- No support for site: operators (SearXNG doesn't proxy them cleanly)
- Cached (5min TTL) — fine for pre-research

### Step 0.75 (Query Plan) — You Are the Planner

Generate a JSON plan file via heredoc. **The quoted `'PLAN_EOF'` marker is load-bearing** — apostrophes in search/ranking strings break unquoted heredocs:

```bash
QUERY_PLAN_FILE=$(mktemp "${TMPDIR:-/tmp}/last30days-plan.XXXXXX")
trap 'rm -f "$QUERY_PLAN_FILE"' EXIT
cat > "$QUERY_PLAN_FILE" <<'PLAN_EOF'
{
  "intent": "how_to",
  "freshness_mode": "evergreen_ok",
  "cluster_mode": "workflow",
  "subqueries": [
    {
      "label": "primary",
      "search_query": "topic search terms here",
      "ranking_query": "Natural language question about the topic?",
      "sources": ["reddit", "x", "youtube", "hackernews"],
      "weight": 1.0
    }
  ]
}
PLAN_EOF
```

Sources available to primary subquery: `reddit, x, youtube, tiktok, instagram, hackernews, polymarket`. The engine silently drops platforms with no configured credentials — no error, just thinner output.

### Step 1 (Engine Execution)

```bash
"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" "{TOPIC_STRING}" \
  --emit=compact \
  --save-dir="${LAST30DAYS_MEMORY_DIR}" \
  --save-suffix=v3 \
  --plan "$QUERY_PLAN_FILE" \
  --subreddits=selfimprovement,Biohackers,socialskills  \
  --days=60
```

Resolved targeting flags (all optional, omit if un-resolved):
- `--x-handle={handle}` — primary X account
- `--x-related={h1,h2}` — associated handles (company, commentators)
- `--subreddits={sub1,sub2}` — comma-separated, no `r/` prefix
- `--github-user={user}` — person-mode GitHub (person topics)
- `--github-repo={owner/repo}` — project-mode GitHub (product topics)
- `--tiktok-hashtags={h1,h2}` — inferred, not searched
- `--tiktok-creators={c1}` — creator/influencer topics only
- `--ig-creators={c1}` — creator/brand topics only
- `--days=N` — lookback window (default 30). Use `--days=60` when the topic is evergreen/self-help and needs more data.

**Timeout:** Use 420s (7 min) — the engine runs Reddit RSS + HN Algolia + internal ranking, typically 45-90s on this hardware.

### Step 2 (Supplements) — Use SearXNG

After the engine finishes, run 2-3 SearXNG searches to fill blog/doc/news depth:

```python
from hermes_tools import mcp__searxng__web_search
# Run 2-3 searches for supplement depth
mcp__searxng__web_search(query="targeted supplement query")
```

**SearXNG tip for supplements:** Simple, generic queries work better than very specific ones. Broad terms like "brain exercises memory" or "speech fluency techniques" return more useful results than multi-word specific queries. Add `reddit` to the query when you want community content that the engine may have missed.

### Step 2.5 (Save Appendix)

Append supplement results to the engine's saved raw file (located via the `[last30days] Saved output to` log line):

```bash
cat >> {RAW_FILE_PATH} <<'APPEND_EOF'

## WebSearch Supplemental Results

- **Publisher** (domain.com) — 1-2 sentence excerpt of what you found.
- **Publisher** (domain2.com) — 1-2 sentence excerpt.
APPEND_EOF
```

Use the canonical bullet format: `- **{Publisher}** ({domain}) — {1-2 sentence excerpt}`.

### Output Contract (LAWs distilled)

The skill has a complex output contract. Key rules:
1. **Badge on line 1**: `🌐 last30days vVERSION · synced YYYY-MM-DD` — pass through from engine
2. **No `Sources:` block** at end — the emoji-tree footer IS the citation
3. **No `##` section headers** in body (exception: comparison queries)
4. **No em-dashes** — use ` - ` (hyphen with spaces)
5. **Inline markdown links** for all citations — `[name](url)`, never raw URLs
6. **Engine footer pass-through verbatim** — bounded by `---`, starts with `✅ All agents reported back!`
7. **Transform evidence clusters into prose** — never dump raw `### 1. (score N, ...)` blocks to user

## Current Limitations on This System

| Limitation | Impact | Fix |
|------------|--------|-----|
| No X/AUTH_TOKEN/CT0 | X posts = 0 results | Log into x.com in browser OR add XAI_API_KEY |
| No YouTube/yt-dlp | YouTube = 0 results | `pamac install yt-dlp` or `brew install yt-dlp` |
| No ScrapeCreators key | TikTok/IG/Threads = 0 results | Get free key at scrapecreators.com |
| Reddit RSS keyless fallback | Works but scores = 0 for all items | Engine handles this gracefully |
| Firecrawl not configured | web_search/web_extract unavailable | Use SearXNG MCP tools as direct replacement |
| No gh CLI | GitHub = 0 results | Install gh via `pamac install github-cli` |

Despite these limits, Reddit + HN alone produces useful results for most self-improvement, technology, and culture topics. The engine reports quality honestly in its output.
