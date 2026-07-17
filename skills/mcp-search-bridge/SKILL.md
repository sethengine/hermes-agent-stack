---
name: mcp-search-bridge
description: Build and deploy zero-dependency MCP servers for web search + content extraction. Covers SearXNG, Trafilatura, multi-engine fallback, and agent-specific configuration for Hermes, OpenCode, and llama.cpp WebUI.
triggers:
  - User asks to improve, fix, or build an MCP server for web search or extraction
  - User wants free/self-hosted alternatives to Firecrawl, Exa, Brave Search
  - User needs MCP tools working across multiple agent platforms
  - User asks about SearXNG, Trafilatura, or content extraction for LLMs
---

# MCP Search Bridge

Build a single Python MCP server that provides web search and content extraction across all agent platforms — Hermes, OpenCode, Claude Desktop, and llama.cpp WebUI.

## Architecture

One file, two transports, four tools, zero API keys:

```
~/.local/bin/mcp-bridge
├── stdio mode (default)      → Hermes, OpenCode, Claude Desktop
└── --http-port PORT mode      → llama.cpp WebUI, browser clients
```

**Tools:**
- `web_search` — cached multi-engine with fuzzy dedup + category-aware ranking
- `web_extract` — page extraction (Trafilatura preferred, HTML fallback, 10min TTL)
- `news_search` — news headlines (SearXNG news category)
- `scholar_search` — academic papers (arXiv API)
- `research_plan` — automated multi-query research with cross-source synthesis

## Dependencies

**Zero required.** Python 3.11+ stdlib only. Optional upgrades:

| Library | What it improves | Install | Notes |
|---|---|---|---|
| `httpx` | Faster HTTP with keepalive | `pip install httpx` | Auto-detected |
| `trafilatura` | Best-in-class extraction (HuggingFace/IBM/MS use it) | `pip install trafilatura` | Typically python3.14+ only; use `python3.14` explicitly for HTTP mode |

The bridge auto-detects each — no config needed. Falls back to urllib + basic HTML stripping when absent.

## Pitfalls

### DO NOT add non-search tools
User wants search improvements only. Weather, calculator, currency, time, DNS — these are NOT search and will be rejected. This happened once and was called "crap." Scope is: search, extract, news, scholar. Nothing else.

### llama.cpp WebUI: CORS + proxy toggle
The WebUI MCP client runs in the browser and needs HTTP transport. The bridge's `--http-port` mode handles this. Two critical gotchas:
1. **"Use llama-server proxy" toggle only appears in EDIT mode**, not when first adding a server. Save first, then edit to find it.
2. **The proxy toggle must be ON** unless the bridge and WebUI are on the same origin (rare). Without it, cross-origin browser requests fail with "Failed to fetch" in 3ms (blocked before sending).

llama-server must be started with `--ui-mcp-proxy` flag.

### After config changes: new session required
Hermes config updates (`hermes mcp add/remove`) take effect on next session start. Tools available in the current session are from the old process.

## Search pipeline

```
web_search(query)
  ├─ Cache check (TTL 300s, SHA-256 keyed) — instant return on hit
  ├─ SearXNG (primary: 93 engines — Google, DDG, Brave, Wikipedia, arXiv, GitHub, YT...)
  │   └─ FAIL → DuckDuckGo Lite (HTML scraping, free)
  ├─ Wikipedia API (always: 3 results, lower weight)
  ├─ arXiv API (if query contains tech/academic keywords)
  ├─ Fuzzy dedup (trigram Jaccard similarity, threshold 0.85)
  └─ Category-aware ranking (tech → boosts GitHub/arXiv; news → boosts Reuters/Bing)
```

## Cache layer

In-process TTL cache using `OrderedDict` + `threading.Lock`:
- **Search**: 300s TTL, 200-entry LRU, keyed by SHA-256(normalized params JSON)
- **Extract**: 600s TTL, 100-entry LRU
- Cache hits return in <1ms — eliminates redundant SearXNG roundtrips
- Thread-safe via lock acquisition on get/set

For SearXNG-level caching (benefits all clients), enable ValKey/Redis:
```yaml
# settings.yml
valkey:
  url: valkey://localhost:6379/0
```
Bind ValKey to `0.0.0.0` so Docker containers reach it via bridge gateway (`172.17.0.1`). Set `maxmemory-policy allkeys-lru`.

## Fuzzy deduplication

Trigram Jaccard similarity on titles, threshold 0.85. Different engines return the same page with subtly different titles — this catches them. Strips common suffixes (` | ...`, ` - ...`) before comparison.

## Category-aware ranking

Applies boosts based on `context` parameter:
- **tech**: GitHub +0.20, StackOverflow +0.15, arXiv +0.15
- **news**: Reuters +0.15, Yahoo News +0.10, Wikinews +0.15
- **scholar**: arXiv +0.25, Semantic Scholar +0.20, PubMed +0.20

Base engine boosts: arXiv +0.15, GitHub +0.10, Wikipedia +0.05.

## research_plan tool

Automated multi-query structured research. Derives sub-queries from input, searches each with context-appropriate categories, cross-deduplicates across all results, returns structured synthesis with confidence scores.

Query derivation rules:
- **Comparison** ("X vs Y") → per-entity queries + head-to-head
- **Recommendation** ("best X") → reviews + news + technical specs
- **How-to** ("how to X") → tutorials + troubleshooting
- **General** → overview + latest news + academic perspective

Depth: quick (2 sub-queries), standard (3-4), deep (5-6).

## Content extraction pipeline

```
web_extract(url)
  ├─ HTTP fetch (direct)
  └─ Extract:
      ├─ Trafilatura (if installed, python3.14+) — clean Markdown + metadata
      └─ Fallback: basic HTML stripper (stdlib)
```

Trafilatura extracts: title, author, date, hostname, main text (markdown), tables, structure. Output includes metadata header and extraction method used. **Start the HTTP server explicitly with `python3.14`** to get Trafilatura quality: `python3.14 ~/.local/bin/mcp-bridge --http-port 8090`.

## Agent-specific configuration

### Hermes
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  searxng:
    command: /usr/bin/python3        # or just the bridge if no venv issues
    args:
      - /home/sethengine/.local/bin/mcp-bridge
    enabled: true
```

Use `/usr/bin/python3` explicitly if optional deps (trafilatura) are installed there but not in the venv.

### OpenCode
```json
{
  "mcpServers": {
    "searxng": {
      "type": "stdio",
      "command": "/home/sethengine/.local/bin/mcp-bridge"
    }
  }
}
```

### llama.cpp WebUI
1. Start bridge: `python3 ~/.local/bin/mcp-bridge --http-port 8090`
2. Start llama-server: `llama-server --jinja --ui-mcp-proxy -m model.gguf`
3. WebUI → MCP Servers → Add: URL = `http://127.0.0.1:8090/mcp`
4. Save, then EDIT the server, toggle "Use llama-server proxy" ON

### Claude Desktop
```json
{
  "mcpServers": {
    "searxng": {
      "command": "python3",
      "args": ["/home/sethengine/.local/bin/mcp-bridge"]
    }
  }
}
```

## SearXNG timeout tuning (critical for agent reliability)

The default SearXNG config has `request_timeout: 3.0` — this is the #1 cause of empty/half-empty search results for agents. Many engines need 4-6s. Apply with sudo (Docker volumes are root-owned):

```bash
sudo sed -i \
  -e 's/ban_time_on_fail: 5/ban_time_on_fail: 3/' \
  -e 's/max_ban_time_on_fail: 120/max_ban_time_on_fail: 60/' \
  -e 's/SearxEngineAccessDenied: 180/SearxEngineAccessDenied: 120/' \
  -e 's/SearxEngineTooManyRequests: 180/SearxEngineTooManyRequests: 120/' \
  -e 's/recaptcha_SearxEngineCaptcha: 604800/recaptcha_SearxEngineCaptcha: 3600/' \
  -e 's/request_timeout: 3.0/request_timeout: 6.0/' \
  -e 's/pool_maxsize: 20/pool_maxsize: 50/' \
  -e "s/http_protocol_version: \"1.0\"/http_protocol_version: \"1.1\"/" \
  /home/sethengine/searxng/config/settings.yml

docker restart searxng-new
```

| Setting | Before | After | Why |
|---|---|---|---|
| `ban_time_on_fail` | 5s | 3s | Engines recover faster after transient errors |
| `max_ban_time_on_fail` | 120s | 60s | Cap ban escalation at 1min |
| `SearxEngineAccessDenied` | 3min | 2min | Shorter 403 suspension |
| `SearxEngineTooManyRequests` | 3min | 2min | Shorter 429 suspension |
| `recaptcha_SearxEngineCaptcha` | 7 days | 1 hour | Don't kill engines for a week from one captcha |
| `request_timeout` | 3s | 6s | Fewer timeouts — was #1 cause of empty results |
| `pool_maxsize` | 20 | 50 | More parallel engine requests = faster |
| `http_protocol_version` | 1.0 | 1.1 | Keepalive connections = less TCP overhead |

## SearXNG caching (ValKey/Redis)

For searches that multiple agents repeat, enable the ValKey cache in SearXNG settings.yml and wire the Docker container to the host:

```bash
sudo pacman -S valkey
sudo systemctl enable --now valkey
sudo tee /etc/valkey/valkey.conf > /dev/null << 'EOF'
bind 0.0.0.0
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""
EOF
sudo systemctl restart valkey

# Recreate SearXNG Docker with ValKey env var
docker stop searxng-new && docker rm searxng-new
docker run -d --name searxng-new \
  -p 8081:8080 \
  -v /home/sethengine/searxng/config:/etc/searxng \
  -v /home/sethengine/searxng/data:/var/cache/searxng \
  -e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0 \
  searxng/searxng:latest
```

The bridge's in-process LRU cache (5min/10min TTL) handles per-process caching; ValKey adds cross-process/restart caching at the engine level.

## Cross-profile deployment

When updating the MCP bridge, sync all Hermes profiles:

```bash
echo "y" | hermes mcp remove searxng && echo "y" | hermes mcp add searxng --command /home/sethengine/.local/bin/mcp-bridge
```

For OpenCode config, use `python3.14` explicitly for Trafilatura quality:

```json
{"mcp": {"searxng": {"type": "local", "command": ["python3.14", "/home/sethengine/.local/bin/mcp-bridge"], "enabled": true}}}
```

## SearXNG engines

98 engines enabled by default. Key engines for LLM work:
- **general**: google, duckduckgo, brave, startpage, wikipedia
- **news**: google news, bing news, reuters, yahoo news
- **science**: arxiv, google scholar, semantic scholar, pubmed
- **code**: github, stackoverflow, docker hub, pypi
- **social**: lemmy, mastodon, reddit (via plugin)

Tuning: increase `outgoing.request_timeout` and `outgoing.max_request_timeout` in settings.yml for deeper results. Enable `search.autocomplete` plugin.
