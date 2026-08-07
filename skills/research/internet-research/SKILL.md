---
name: internet-research
description: "Full-spectrum internet research for Hermes: search strategy, source verification, deep-dive investigation, cross-referencing, and structured synthesis. Covers tech, news, academic, people, market, and domain-specific research with reusable scripts and templates."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Internet, Search, Fact-Checking, Source-Verification, Deep-Research, Synthesis, OSINT]
    related_skills: [git-repo-research, research-assistant, writing-plans, subagent-driven-development]
---

# Internet Research

Full-spectrum internet research methodology for Hermes agents. Go from a raw question to a verified, synthesized report using web search, extraction, browser inspection, and cross-referencing.

---

## Table of Contents

1. [Research Methodology](#1-research-methodology)
2. [Search Strategy & Operators](#2-search-strategy--operators)
3. [Source Types & Handling](#3-source-types--handling)
4. [Fact-Checking & Verification](#4-fact-checking--verification)
5. [Deep Research Techniques](#5-deep-research-techniques)
6. [Domain-Specific Research](#6-domain-specific-research)
7. [Synthesis & Reporting](#7-synthesis--reporting)
8. [Pitfalls & Anti-Patterns](#8-pitfalls--anti-patterns)
9. [Reference Templates](#9-reference-templates)
10. [Reusable Scripts](#10-reusable-scripts)

---

## 1. Research Methodology

### The Research Loop

Research is iterative. Always follow this loop:

```
QUESTION → SEARCH → EXTRACT → EVALUATE → SYNTHESIZE → (GAP? → SEARCH) → ANSWER
```

### Phase Breakdown

| Phase | What you do | Tools |
|-------|-------------|-------|
| **Frame** | Define the question, scope, and target answer format | — |
| **Search** | Run targeted queries across sources | `web_search`, `browser_navigate` |
| **Extract** | Pull content from promising results | `web_extract`, `browser_snapshot`, `curl` |
| **Evaluate** | Assess credibility, freshness, relevance | See §4 |
| **Synthesize** | Combine into structured answer | See §7 |
| **Gap check** | Identify missing info → loop back to Search | — |

### Before You Start — Frame the Research

Always clarify:

```
Q1: What exactly am I trying to find out?
     → A specific fact / an overview / a comparison / a trend?

Q2: What's the scope?
     → Timeframe (last month / last year / all time)?
     → Depth (quick fact-check / thorough investigation)?

Q3: What would a good answer look like?
     → Single number / table / report / recommendation?

Q4: What sources are likely authoritative?
     → Official docs / academic papers / news / forums / social media?
```

**Pro tip:** When the user's question is vague or open-ended, use the framing questions (via `clarify` or reasoning) before diving into search.

---

## 2. Search Strategy & Operators

### Query Structure

Build queries from these building blocks:

```
[CORE CONCEPT] + [QUALIFIER] + [SOURCE/TYPE] + [EXCLUDE NOISE]
```

Examples:
```
"transformer architecture" tutorial site:arxiv.org
MQTT broker performance benchmark github.com 2025
"reinforcement learning" "reward model" -game -playing
```

### Advanced web_search Operators

These may work depending on the backend (Google, SearXNG, etc.):

| Operator | Purpose | Example |
|----------|---------|---------|
| `"exact phrase"` | Force exact match | `"retrieval augmented generation"` |
| `site:` | Restrict to domain | `site:github.com agent framework` |
| `site:*.edu` | Academic domains | `site:*.edu LLM reasoning` |
| `intitle:` | Word in title | `intitle:survey transformer attention` |
| `inurl:` | Word in URL | `inurl:arxiv RAG` |
| `filetype:pdf` | File type | `filetype:pdf attention is all you need` |
| `-term` | Exclude term | `agent -real-estate -travel` |
| `term OR term` | Either/or | `PyTorch OR JAX` |
| `AROUND(n)` | Proximity | `transformers AROUND(3) attention` |
| `after:` / `before:` | Date range | `after:2024-01-01 LLM agents` |
| `source:n` | Specific backend | `source:news LLM regulation` |
| `related:` | Similar sites | `related:github.com/langchain-ai/langchain` |

### Fallback Search: x_search When web_search Is Unavailable

When `web_search` fails (e.g. no FIRECRAWL_API_KEY configured), use `x_search` as a capable alternative:

```python
# Basic query — same syntax as web_search
x_search("Chrome hardware video acceleration Linux NVIDIA Wayland 2026")

# Date-filtered (use it instead of after:/before:)
x_search("topic of interest", from_date="2026-01-01")

# Account-specific
x_search("topic from:handle")
x_search("topic to:handle")
```

**Strengths of x_search:**
- Excellent for current events, technical discussions, and community sentiment
- Can filter by date range (handy for "last 30 days" queries)
- Works with XAI credentials — often available even when web_search backends aren't
- Returns structured responses with inline citations

**Limitations of x_search:**
- X-only — you miss Reddit, HN, blogs, official docs. Use it as a complement, not a full replacement.
- No site: or filetype: operators — you can't filter by domain
- Results are conversational, not document-based — treat as leads, not primary sources
- The model does its own synthesis — cross-reference any factual claims with other sources

**When to reach for x_search:**
- `web_search` is throwing "not configured" errors → x_search is the immediate fallback
- You need real-time / breaking coverage (product launches, outages, policy changes)
- You want community reaction or sentiment on a topic
- The subject has active technical discussion on X (Linux, ML/AI, crypto, open source)
- Researching claims made *on X* specifically

**Never use x_search as the sole source** for factual claims about software configuration, APIs, or documentation — always verify against primary sources via web_extract or browser.

### Fallback: Direct GitHub Access When All Search Engines Are Blocked

When `web_search` is not configured AND search engines (DuckDuckGo, Google, Bing) CAPTCHA-block the browser, you can often still reach GitHub repos directly:

```python
# Known repos work — GitHub doesn't CAPTCHA the browser tool
browser_navigate("https://github.com/owner/repo")
```

From the repo page:
- **Star count, fork count, last commit** are visible in the snapshot — use these to gauge activity/credibility
- **README content** is available via `browser_console(expression="document.body.innerText.substring(0, 10000)")` or by navigating to the raw URL `https://raw.githubusercontent.com/owner/repo/branch/README.md`

**Useful for:** Researching projects when you already have leads from your knowledge — navigate directly to candidates to verify their existence, activity level, and quality rather than relying on search.

**Limitation:** You need to *know* the repo name already. This doesn't replace discovery search — it replaces *verification* when discovery can't happen.

### Discovery Through GitHub Topics & Search

When you DON'T have leads but GitHub auth is still working, use GitHub's own discovery surface:

```python
# Browse repos by topic — sorted by recency
browser_navigate("https://github.com/topics/hermes-agent?o=desc&s=updated")
browser_navigate("https://github.com/topics/mcp?o=desc&s=stars")

# Search GitHub for awesome lists specifically
browser_navigate(
    "https://github.com/search?q=awesome+{niche}&type=repositories&s=updated&o=desc"
)

# Search for skill / MCP / workflow repositories
browser_navigate(
    "https://github.com/search?q={platform}+skills+MCP&type=repositories&s=stars&o=desc"
)
```

**Topic pages** (`/topics/{tag}`) are especially useful — they show the total repo count (e.g. "1,318 public repositories" for `hermes-agent`), each with star count, description, and topic tags. Sort by "Recently updated" to find actively maintained projects.

**Search results** show star counts, fork counts, and a one-line summary. Use `s=stars` for quality-first or `s=updated` for freshness-first.

### Hacker News Research (Algolia)

For community discussion and discovery, use HN Algolia (bypasses most bot detection):

```python
# Search stories by date range
browser_navigate(
    "https://hn.algolia.com/?q={query}&sort=byDate&type=story&dateRange=lastMonth"
)

# Search all content (stories + comments)
browser_navigate(
    "https://hn.algolia.com/?q={query}&sort=byDate&type=all&dateRange=all"
)
```

HN Algolia is good for surfacing Show HN posts for new tools, Ask HN discussions, and community sentiment. The accessibility tree renders story titles as links with point counts and comment counts.

### C4AI Fallback: Research When All Search Tools Are Down

When every primary search tool fails (no FIRECRAWL_API_KEY, XAI credits exhausted, Brave/SearXNG MCP closed), use the **C4AI MCP tools** (`mcp_c4ai_md`, `mcp_c4ai_crawl`) combined with `execute_code` for HTML text extraction from login-walled pages.

**The full resilience chain (try in order):**
1. `web_search` / `web_extract` (Firecrawl)
2. `x_search` (XAI)
3. Brave MCP / SearXNG MCP
4. Playwright browser — may hit CAPTCHA/login walls
5. **C4AI `crawl`** on old.reddit.com — bypasses JS challenges
6. **C4AI `md`** with `filter=fit` for content / `filter=raw` for full page
7. `execute_code` with regex to extract text from double-JSON-wrapped HTML

**Why old.reddit.com:** Old Reddit bypasses Cloudflare/JS challenges that block new Reddit. The C4AI crawler fetches it cleanly.

**Thread listing pages** — use `mcp_c4ai_md` on old Reddit listing URLs:
```python
from hermes_tools import mcp_c4ai_md
result = mcp_c4ai_md(url="https://old.reddit.com/r/subreddit/comments/?sort=new&t=month")
```
Returns post titles, authors, scores, and comment counts without login.

**Comment extraction from login-walled threads** — full HTML crawl + regex:
```python
import re, json
from hermes_tools import mcp_c4ai_crawl, read_file

# Step 1: fetch via C4AI crawl (result auto-saved to /tmp/hermes-results/)
result = mcp_c4ai_crawl(urls=["https://old.reddit.com/r/subreddit/comments/.../?sort=top"])

# Step 2: read the persisted output from the tool result path
raw = read_file(path="/tmp/hermes-results/call_xxx.txt", limit=10)

# Step 3: parse double-JSON wrapper
outer = json.loads(raw["content"])
inner = json.loads(outer["result"])
html = inner["results"][0]["html"]

# Step 4: extract comment bodies
usertexts = list(re.finditer(
    r'<div class="usertext-body may-blank-within md-container ">', html
))
for m in usertexts:
    start = m.end()
    md_start = html.find('<div class="md">', start)
    if md_start != -1 and md_start < start + 800:
        md_end = html.find('</div>', md_start)
        if md_end != -1:
            before = html[max(0, m.start()-1200):m.start()]
            author = re.search(r'<a[^>]*class="author"[^>]*>([^<]+)</a>', before)
            score = re.search(r'<span[^>]*class="score[^"]*"[^>]*>([^<]+)</span>', before)
            content = html[md_start:md_end+6]
            text = re.sub(r'<[^>]+>', '', content)
            text = text.replace('&#x200B;', '').replace('&amp;', '&')
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 5:
                print(f"--- {author.group(1) if author else '?'} ({score.group(1) if score else '?'}) ---")
                print(text[:500])
```

C4AI `md` filter options: `f=fit` (trim noise), `f=raw` (full page), `f=bm25` (with `q` query), `f=llm` (LLM-extracted). For login-walled Reddit, `fit` usually returns only sidebar — use `crawl` + regex for full comment extraction.

**Limitations:** Need to manually parse the double-JSON wrapper. Author/score extraction via regex is fragile. Deep comment nesting may truncate. Doesn't bypass aggressive anti-bot systems. C4AI rate limits apply for large crawls. Use the `crawl` result path from the tool output to locate the persisted file.

### Community-Curated Resource Discovery Methodology

When researching "best free resources for X" — especially agent tooling, MCP servers, skills — follow this pattern:

1. **GitHub Topics** first — browse `/topics/{relevant-tag}` sorted by updated. This surfaces actively maintained repos organized by community tagging.
2. **GitHub Search for awesome lists** — search `awesome {topic}` sorted by stars. Awesome lists are community-curated directories that save you from surveying every repo individually.
3. **Cross-reference with HN Algolia** — search the same topic on HN to find which repos have real community discussion (Show HNs, Ask HNs).
4. **Verify individual repos** — for each candidate surfaced above, navigate directly to verify: last commit date, star count, issue activity, and README quality.
5. **Distinguish community-curated from company sources** — the user may explicitly want "curated by people, not by companies." Community-curated sources are: awesome lists on GitHub, subreddit wikis, HN threads, personal blogs, Discord community pins. Company sources are: official docs, vendor blogs, product websites. Ask or infer which they want.

### Query Templates by Goal

```python
# Overview / discovery
web_search("what is {topic} overview 2025")
web_search("{topic} explained beginners")

# Latest developments
web_search("{topic} 2025 update latest")
web_search("{topic} news after:2025-01-01")

# Comparison
web_search("{topic} vs {alternative} comparison")
web_search("best {topic} alternatives open source 2025")

# Deep technical
web_search("{topic} architecture implementation guide")
web_search("{topic} benchmark performance comparison")

# Problem-solving
web_search("{topic} error solution fix")
web_search("{topic} common pitfalls gotchas")

# Community pulse
web_search("reddit {topic} recommendations")
web_search("HN {topic} discussion")
web_search("stackoverflow {topic}")
```

### Multi-Angle Search

Always search from 3+ angles — never trust a single result:

```python
# Angle 1: Official / primary sources
web_search("site:{project}.io {topic} documentation")

# Angle 2: Technical deep-dive
web_search("{topic} implementation guide tutorial")

# Angle 3: Community / anecdotal
web_search("{topic} reddit discussion experience")

# Angle 4: Critical / negative
web_search("{topic} limitations problems issues")
web_search("{topic} alternatives why not use")
```

---

## 3. Source Types & Handling

### Source Credibility Pyramid

```
        ⬆ HIGH
    Peer-reviewed papers
    Official documentation (docs.official.io)
    Government / .gov / .mil sources
    Standards bodies (ISO, IETF, W3C)
    Established news (Reuters, AP, Bloomberg)
    Technical blogs from known authors
    Vendor / company blogs
    Community wikis (MDN, Wikipedia)
    forums (Stack Overflow, Reddit)
    Social media / X / personal blogs
        ⬇ LOW
```

### Handling Each Source Type

#### Academic papers (arXiv, ACL, NeurIPS)
```python
# Use web_extract on arXiv abstract
web_extract("https://arxiv.org/abs/2303.18223")

# Download PDF for deep reading
terminal("curl -O https://arxiv.org/pdf/2303.18223.pdf")
```

**Check:** Published venue, citation count, author affiliations, date.

#### Official documentation
```python
# Docs sites — extract content
web_extract("https://docs.example.com/getting-started")

# Raw markdown from GitHub repos
web_extract("https://raw.githubusercontent.com/owner/repo/main/README.md")
```

**Check:** Version, last update date, deprecation notices.

#### News articles
```python
# Search with recency
web_search("{topic} site:reuters.com after:2025-01-01")
web_search("{topic} site:bloomberg.com")

# For paywalled articles, research through summaries/cross-references
```

**Check:** Publication date, author, outlet reputation, corroborating sources.

#### Technical blogs
```python
# Find blog posts
web_search("{topic} site:medium.com OR site:towardsdatascience.com")
web_search("{topic} blog tutorial")
```

**Check:** Author expertise, date (old ML blog posts age poorly), comments.

#### Forums & Q&A
```python
# Stack Overflow
web_search("site:stackoverflow.com {topic}")

# Reddit — filter by subreddit
web_search("site:reddit.com/r/{subreddit} {topic}")
```

**Check:** Accepted answers, vote scores, date, whether it's the top result.

#### Social media / X
```python
# Via x_search
x_search("{topic} from:handle")
```

**Use only for:** breaking news, community sentiment, first-hand accounts. Never as primary evidence for factual claims.

### When to Use Browser vs web_extract

| Situation | Tool | Why |
|-----------|------|-----|
| Plain-text URL (`.md`, `.txt`, API response) | `web_extract` or `curl` | Fast, no JS overhead |
| Known documentation site | `web_extract` | Structured markdown |
| GitHub raw content | `web_extract` on `raw.githubusercontent.com` | Direct markdown |
| JavaScript-rendered page | `browser_navigate` | Must execute JS |
| Interactive elements (forms, clicks) | `browser_*` | Need to navigate UI |
| Page behind auth wall | Try `web_extract` first | Sometimes works without JS |

### Extracting Text from Raw/Plain Pages via Browser

When `web_extract` is unconfigured (no FIRECRAWL_API_KEY) and the accessibility tree snapshot shows a sparse or empty page (e.g. raw.githubusercontent.com pages), use `browser_console` with a JavaScript expression to extract content:

```python
# Navigate to the raw/plain page first
browser_navigate("https://raw.githubusercontent.com/owner/repo/branch/README.md")

# Extract the visible text via JS
result = browser_console(
    expression="document.body.innerText.substring(0, 10000)"
)
```

This bypasses the accessibility tree limitations and works on any page where the DOM exists but the snapshot doesn't render text.

---

## 4. Fact-Checking & Verification

### The CRAAP Test

| Criterion | Ask | Red Flag |
|-----------|-----|----------|
| **C**urrency | When was this published/updated? | No date, or >3y old for tech | 
| **R**elevance | Does this address the question? | Topic-adjacent but not on-point |
| **A**uthority | Who wrote it? Are they qualified? | No author, unknown source, no credentials |
| **A**ccuracy | Is it supported by evidence? | Unsourced claims, logical gaps |
| **P**urpose | Why does this exist (inform/persuade/sell)? | Overt bias, product placement |

### Cross-Reference Protocol

Never trust a single source. Always:

1. **Triangulate**: Find 2+ independent sources that agree on the same fact.
2. **Trace the chain**: Follow citations back to the original claim/source.
3. **Check the date**: In fast-moving fields (ML, security, JS frameworks), a 6-month-old article can be dangerously outdated.
4. **Look for retractions/corrections**: Search `"{title}" retraction` or `"{title}" correction`.
5. **Check the domain**: `example.com` vs `example.org` vs `example-news.com` (suspicious).

### Quick Credibility Check Script

```python
from hermes_tools import web_search

def check_source(url_or_domain):
    """Quick credibility signals for a source."""
    domain = url_or_domain.split("/")[2] if "//" in url_or_domain else url_or_domain
    
    # Check for known reliable domains
    trusted = {
        "reuters.com", "ap.org", "bloomberg.com", "nature.com", 
        "science.org", "arxiv.org", "github.com", "wikipedia.org",
        "nytimes.com", "wsj.com", "economist.com", "ieee.org",
        "acm.org", "stanford.edu", "mit.edu", "cam.ac.uk",
        "docs.", "developer.mozilla.org",
    }
    suspicious = {
        "dailymail.co.uk", "infowars.com", "breitbart.com",
        "zerohedge.com", "naturalnews.com", "beforeitsnews.com",
    }
    
    if any(t in domain for t in trusted):
        return "🟢 Likely reliable"
    if any(s in domain for s in suspicious):
        return "🔴 Questionable — verify claims independently"
    
    # Unknown domain — check further
    results = web_search(f"site:{domain} credibility OR reputation OR review")
    return f"🟡 Unknown — investigate further. Search results: {len(results)} hits"
```

### Claim Decomposition

When you see a factual claim, decompose it:

```
Claim: "Model X achieves 99.5% accuracy on benchmark Y"

Decompose:
├── What benchmark Y? (version, split, eval protocol?)
├── Who reported this? (paper author, vendor blog, social media?)
├── When was it measured? (benchmarks change over time)
├── Against what baseline? (comparable settings?)
└── Is it reproduced? (independent verification?)
```

### Number/Stat Verification

- **API/TOU changes**: Always check the actual policy page, not summaries.
- **Pricing**: Check the actual pricing page, not blog posts.
- **Benchmarks**: Check the specific benchmark paper/leaderboard, not cherry-picked vendor claims.
- **Dates**: Always note as-of dates for any time-sensitive data.

---

## 5. Deep Research Techniques

### Citation Chaining (Forward & Backward)

```python
# Start with one solid paper/article
# Then:
# BACKWARD: Search for papers it cites
web_search('"cited paper title" 2024')

# FORWARD: Search for papers that cite it
web_search('"influential paper title" follow-up')
web_search('"influential paper title" subsequent work')
```

### Lateral Searching

When you hit a dead end, pivot laterally:

```
Dead end: "quantum transformer" → few results
Lateral 1: "quantum machine learning attention mechanism"
Lateral 2: "quantum natural language processing"
Lateral 3: "variational quantum circuits NLP"
```

### The Wikipedia Pipeline

Wikipedia is rarely a final source — it's a **launchpad**:

```python
# Step 1: Get the Wikipedia overview
web_extract("https://en.wikipedia.org/wiki/Retrieval-augmented_generation")

# Step 2: Mine the references section at the bottom
# (Every Wikipedia article has primary sources linked)

# Step 3: Follow the most promising references
web_extract("https://arxiv.org/abs/2005.11401")  # original RAG paper
```

### Subagent-Driven Parallel Research

For complex multi-faceted topics, parallelise with `delegate_task`:

```python
from hermes_tools import delegate_task

tasks = [
    {
        "goal": "Research security concerns",
        "context": f"Research security vulnerabilities and concerns about {topic}. Focus on CVE entries, security advisories, and known attack vectors.",
        "toolsets": ["web"]
    },
    {
        "goal": "Research performance benchmarks",
        "context": f"Research performance benchmarks for {topic}. Look for independent benchmarks, not vendor claims.",
        "toolsets": ["web"]
    },
    {
        "goal": "Research community adoption",
        "context": f"Research community adoption trends for {topic}. Look for usage stats, company case studies, and ecosystem health.",
        "toolsets": ["web"]
    }
]

results = delegate_task(tasks=tasks)
```

### Temporal Analysis

For topics that evolve, build a timeline:

```python
# Search by year to see evolution
web_search("{topic} 2022")
web_search("{topic} 2023")  
web_search("{topic} 2024")
web_search("{topic} 2025")

# Then identify inflection points:
# - When did interest spike?
# - When did major players enter?
# - When did the landscape change?
```

### Wayback Machine

For dead/404 pages or to see how a page changed:

```python
# Check Wayback Machine
web_extract("https://web.archive.org/web/20250101000000/https://example.com/page")

# Or search for cached versions
web_search("cache:https://example.com/page")
web_search("site:web.archive.org example.com")
```

---

## 6. Domain-Specific Research

### Linux Gaming / ProtonDB Research

For game compatibility research on Linux (Proton, Wine, native), ProtonDB is the canonical source but requires JS rendering:

```
# Step 1: Use Playwright to load the ProtonDB page (React SPA — web_extract won't work)
browser_navigate(f"https://www.protondb.com/app/{steam_app_id}")

# Step 2: Wait for the React app to hydrate and fetch reports
browser_wait(time=5)

# Step 3: Capture the full accessibility tree snapshot
snapshot = browser_snapshot()
```

The snapshot contains structured report data including: rating, Steam Deck status, individual user reports with date, Proton version, distro, kernel, GPU, driver, RAM, CPU, and report text with tinker steps/bugs/workarounds.

**Extracting report text from the snapshot:** Look for `heading` elements (report titles), `paragraph` elements (report body), `code` blocks after launch options mentions, and `link` elements with relative dates ("1 month ago"). User hardware metadata follows labels like `Proton X.Y-Z`, `Distro:`, `Kernel:`, `GPU Driver:`, etc.

**Key signals when researching NVIDIA + Wayland + Proton settings issues:**
- "Full screen" or "resolution" complaints — common NVIDIA Wayland issue with Proton
- Differences between Proton versions (Proton 10 vs Experimental vs GE-Proton)
- `PROTON_ENABLE_WAYLAND=1` vs `PROTON_ENABLE_WAYLAND=0` in launch options
- "windowed mode works, fullscreen crashes" pattern — specific to NVIDIA Wayland
- Driver version — note NVIDIA 5xx.xx releases

**Common D2R launch options from reports:**
```
-address eu.actual.battle.net    # Server selection (Steam version lacks launcher)
game-performance %command%
PROTON_ENABLE_WAYLAND=1 WAYLANDDRV_PRIMARY_MONITOR=DP-1 %command%
SteamDeck=0 %command%             # Disable Deck controller mode on non-Deck distros
```

### Technology / Software Research

```python
# Version history
web_search("{project} changelog release notes")
web_search("{project} version history")

# Deprecations / breaking changes
web_search("{project} deprecation migration")
web_search("{project} breaking changes upgrade")

# Security
web_search("{project} CVE security vulnerability")
web_search("{project} security advisory")

# Ecosystem
web_search("{project} plugins extensions ecosystem")
web_search("{project} who uses companies case studies")
```

### People / Expert Research

```python
# Publications
web_search("{name} publications papers")

# Talks
web_search("{name} talk conference 2024 2025")
web_search("{name} YouTube presentation")

# Professional background
web_search("{name} LinkedIn profile")
web_search("{name} GitHub")

# Controversies / criticism
web_search("{name} controversy criticism")
```

### Company / Product Research

```python
# Funding & business
web_search("{company} funding round valuation 2025")
web_search("{company} revenue employees")

# Product quality
web_search("{product} review rating")
web_search("{product} complaints issues problems")

# Competition
web_search("{product} competitors alternatives")
web_search("{product} vs {competitor}")

# Leadership
web_search("{company} CEO founder interview")
```

### News / Current Events

```python
# First 24h: social media + wire services
x_search("{event}")
web_search("{event} site:reuters.com OR site:ap.org")

# 24-72h: initial analysis
web_search("{event} analysis")

# 1 week+: investigative pieces
web_search("{event} investigation deep dive")

# Always check multiple outlets from different regions/countries
```

### Health / Medical Research

*Highest verification standards needed.*

```python
# Preferred sources
web_search("{topic} site:who.int")
web_search("{topic} site:cdc.gov")
web_search("{topic} site:pubmed.ncbi.nlm.nih.gov")
web_search("{topic} site:mayoclinic.org")
web_search("{topic} site:cochrane.org")

# Check for retractions
web_search("{paper title} retracted")
web_search("{paper title} correction")

# Beware of
web_search("{claim} myth debunked")
web_search("{claim} fact check")
```

### Legal / Regulatory Research

```python
# Primary sources
web_search("{regulation} site:congress.gov")
web_search("{regulation} site:gov.uk")
web_search("{regulation} site:europa.eu")

# Analysis
web_search("{regulation} analysis summary implications")
web_search("{regulation} effective date compliance deadline")
```

---

## 7. Synthesis & Reporting

### Quick-Fact Format

For simple factual questions:

```markdown
**Answer:** [Direct answer]

**Source:** [URL] — [publication date]
**Confidence:** High / Medium / Low
**Verified by:** [Cross-reference URL 1], [Cross-reference URL 2]
```

### Structured Report Format

```markdown
# Research Report: [Topic]

**Goal:** [What we wanted to find out]
**Date:** [YYYY-MM-DD]
**Status:** Complete / Partial — gaps noted

## Executive Summary
[2-3 sentence synthesis of findings]

## Key Findings

### Finding 1: [Title]
- Evidence: [Source URL]
- Confidence: [High/Medium/Low]
- Notes: [Additional context]

### Finding 2: [Title]
...

## Sources Used
| # | Source | Type | Credibility | Date | Relevance |
|---|--------|------|-------------|------|-----------|
| 1 | [URL] | Paper ✅ | High | 2025-01 | Direct |
| 2 | [URL] | Blog | Medium | 2024-11 | Supporting |
| 3 | [URL] | News | High | 2025-02 | Context |

## Gaps / Further Research
- [Unanswered question 1]
- [Unanswered question 2]

## Methodology
[Briefly describe search process — what was searched, what was excluded]
```

### Comparison Format

```markdown
| Dimension | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| **Ease of use** | ★★★★☆ | ★★☆☆☆ | ★★★★★ |
| **Performance** | 100 req/s | 250 req/s | 80 req/s |
| **License** | MIT (✅) | AGPL (⚠️) | Apache 2.0 (✅) |
| **Last updated** | 2025-03 | 2024-08 | 2025-01 |
| **Community** | 12K stars | 3K stars | 8K stars |
| **Docs** | Excellent | Minimal | Good |

**Verdict:** [Recommendation with reasoning]
```

---

## 8. Pitfalls & Anti-Patterns

### ❌ Common Mistakes

| Pitfall | Why It's Bad | Fix |
|---------|-------------|-----|
| **Single source** | Confirmation bias, missing context | Triangulate 2+ independent sources |
| **Date blindness** | 6-month-old tech info can be wrong | Always check and report dates |
| **Vendor sources** | Cherry-picked favorable data | Seek independent benchmarks |
| **Social media as evidence** | Unverified, viral misinformation | Use only for leads, not proof |
| **Survivorship bias** | Only seeing successful examples | Actively search failures/limitations |
| **LLM-generated pages** | SEO spam, factually wrong | Check authorship, domain history |
| **Confirmation bias** | Searching to prove, not to learn | Search for counter-arguments explicitly |
| **Generic root links** | Giving `github.com` instead of `github.com/owner/repo` or `docs.example.com` instead of `docs.example.com/getting-started` is unactionable | Always include the full path — repo URL, specific doc page, exact resource. Users need to copy-paste, not navigate from a homepage. |
| **Popular-only bias** | Only listing well-known tools misses hidden gems the user asked for | Always search for both "best {topic}" AND "{topic} alternatives" AND "awesome {topic}" to surface lesser-known-but-quality options |

### 🔴 Red Flag Sources

- **Content farms**: `medium.com` (some), `dev.to` (some), generic `.blog` domains
- **AI-generated trash**: Generic writing, wrong specifics, boilerplate phrasing
- **Outdated documentation**: Version 1.x docs for version 3.x software
- **Vendor benchmarks**: Always cherry-pick favorable comparisons
- **Unedited LLM output**: Slick, confident, wrong

### 🟢 Green Flag Sources

- **Official specs** (IETF RFC, W3C, ISO)
- **Peer-reviewed** (preferably with replication)
- **Versioned docs** with changelogs and deprecation notices
- **Primary sources** (original datasets, raw experiment logs)
- **Independent benchmarking** (MLPerf, SPEC, etc.)

---

## 9. Reference Templates

See the `references/` directory for ready-to-use templates:

- `research-brief-template.md` — Use at the start to frame the research
- `source-log-template.md` — Track sources during investigation
- `synthesis-report-template.md` — Output final structured reports
- `local-web-cross-reference.md` — Combine local system inspection with web research for configuration audits
- `agentic-llm-tools-resource-map.md` — Curated directory of free agentic LLM tools, MCP servers, evaluation harnesses, training courses, and news sources. Pre-researched reference for answering "what are the best free resources for X in agentic LLM" questions.
- `hermes-opencode-agent-tooling.md` — Community-curated ready-to-use skills, MCP registries, workflows, and config tweaks specifically for Hermes Agent and OpenCode CLI. Built from browser-based GitHub topic + HN Algolia discovery when web_search was unavailable.
- `c4ai-reddit-comment-extraction.md` — Full working script for extracting comment text from login-walled Reddit threads via C4AI crawl + execute_code. Concrete regex patterns and double-JSON parsing for the resilience fallback chain.
- `last30days-integration.md` — How to run the `last30days` multi-platform social media research engine within Hermes. Covers SearXNG-based pre-research, plan-file generation, engine invocation, supplement workflow, output contract rules, and current credential limitations on this system.

---

## 10. Reusable Scripts

See the `scripts/` directory:

- `source-credibility-check.py` — Quick credibility assessment for a URL
- `research-pipeline.py` — Multi-angle search + extract + synthesize pipeline
- `temporal-analysis.py` — Search a topic year-by-year and build a timeline

---

## Pro Tips

- **Search in rounds**: Round 1 = broad discovery. Round 2 = drill into promising leads. Round 3 = verify and cross-reference.
- **Keep a source log**: Track what you found, where, and how credible. Prevents rework.
- **State confidence levels**: Always tell the user how sure you are. "High" = 2+ independent primary sources agree. "Medium" = one primary source + corroborating secondary. "Low" = single source, forum post, or unverifiable.
- **Know when to stop**: Research can be infinite. Define the "good enough" threshold upfront.
- **Cite URLs concisely**: Use markdown footnotes or inline links. Group same-domain sources.
- **LLM as research partner**: Use the model's knowledge to *guide* search, not to *replace* it. If you know something, verify it — don't assert from parametric knowledge.
- **Respect rate limits**: Many search APIs and sites have rate limits. Batch queries thoughtfully.
- **Use web_extract over browser for text**: browser is 10x slower. Only use browser when JS rendering is required.

## Related Skills

- **agent-search-infrastructure** — Build and configure free, self-hosted MCP search backends (SearXNG tuning, bridge construction, caching). Use this when the search tools themselves need setup or improvement.
- **git-repo-research** — Specialised GitHub repository research (discover, analyze, compare repos)
- **research-assistant** — arXiv papers, blog feeds, prediction markets
- **writing-plans** — Turn research findings into actionable implementation plans
- **subagent-driven-development** — Parallelise research across subagents
