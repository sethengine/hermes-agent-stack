---
name: agent-search-infrastructure
description: "Build and configure free, self-hosted search infrastructure for AI agents. Covers MCP bridge construction, SearXNG tuning, fallback chains, caching, deduplication, ranking, and multi-client transport (Hermes, OpenCode, llama.cpp WebUI). Zero API keys."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Search, MCP, Infrastructure, SearXNG, Caching, Self-Hosted]
    related_skills: [internet-research, research-assistant]
---

# Agent Search Infrastructure

Build free, self-hosted search backends for AI agents (Hermes, OpenCode, Claude Desktop, llama.cpp WebUI). Single-file Python MCP servers, SearXNG optimization, fallback chains, caching, dedup, ranking — zero API keys, zero paid services.

---

## Architecture Pattern

```
AI Agent ──stdio/HTTP──→ mcp-bridge ──REST──→ SearXNG (98 free engines)
                              │                    │
                              ├─ fallback ──→ DuckDuckGo
                              ├─ supplement → Wikipedia
                              ├─ supplement → arXiv (auto, for technical queries)
                              └─ cache (5min TTL), dedup, ranking
```

## MCP Bridge Construction

### Single-File Pattern

One Python file, zero install dependencies. Optional imports auto-detected:

```python
#!/usr/bin/env python3
# Optional deps — auto-detected, graceful fallback
try: import httpx; _HAS_HTTPX = True
except ImportError: _HAS_HTTPX = False
try: import trafilatura; _HAS_TRAF = True
except ImportError: _HAS_TRAF = False
```

### Dual Transport

Same file supports **stdio** (Hermes, OpenCode, Claude Desktop) AND **HTTP** (llama.cpp WebUI, browser clients):

```python
# stdio mode (default, no args)
./mcp-bridge

# HTTP mode (llama.cpp WebUI)
python3.14 ./mcp-bridge --http-port 8090
```

HTTP mode needs CORS headers for browser-based MCP clients:
```python
def _cors(s):
    s.send_header("Access-Control-Allow-Origin", "*")
    s.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
    s.send_header("Access-Control-Allow-Headers",
                  "Content-Type,MCP-Protocol-Version,Mcp-Session-Id,Accept")
```

### HTTP transport contract (what the /mcp endpoint actually is)

The bridge HTTP mode is **simplified stateless JSON-RPC 2.0 over POST** on a single
`/mcp` endpoint — NOT full Streamable-HTTP/SSE:

- `GET /mcp` → server info + tool list (`{"server":"research-bridge","version":"4.0.0","tools":[...]}`)
- `POST /mcp` → JSON-RPC messages (`initialize`, `tools/list`, `tools/call`), JSON back. No session IDs, no SSE stream.
- CORS wide open (`Access-Control-Allow-Origin: *`), so browser pages can call it directly.
- Tools and args: `web_search(query, max_results, page, language, categories, time_range)`, `web_extract(url)`, `news_search(query, time_range)`, `scholar_search(query, max_results)`, `research_plan(query, depth)`.

Client compatibility consequence: works with llama.cpp WebUI (via `--ui-mcp-proxy`
toggle) and simple HTTP clients; a few STRICT MCP clients expect real Streamable-HTTP
session/SSE semantics and will "connect" but never load tools. For those, either proxy
it (llama-server proxy toggle) or call the JSON-RPC directly with curl.

### HTTP bridge persistence (systemd user service)

Run `--http-port` under a user systemd unit, not a background shell. Known-good unit:
`templates/mcp-bridge-http.service` (uses `Restart=always` so it self-heals through
the SearXNG boot race). Install:

```bash
cp ~/.hermes/skills/search/agent-search-infrastructure/templates/mcp-bridge-http.service \
   ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now mcp-bridge-http.service
systemctl --user is-active mcp-bridge-http.service   # → active
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/mcp   # → 200
```

Browser-side interactive test page for the bridge: `templates/mcp-bridge-web.html`
(drop-in, calls `/mcp` with CORS; open via file:// or serve it).

### MCP Handshake

Minimal initialize response (2024-11-05 protocol):
```python
{"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
 "serverInfo": {"name": "bridge-name", "version": "X.Y.Z"}}
```

Handle `notifications/initialized` by returning `None` (notifications have no response). Handle `ping` with empty result `{}`.

## SearXNG Optimization for Agents

### Critical Timeout Tuning

| Setting | Default | Agent-Optimized | Why |
|---------|---------|-----------------|-----|
| `request_timeout` | 3.0s | 6.0s | **#1 cause of empty results** — many engines timeout before responding |
| `ban_time_on_fail` | 5s | 3s | Engines recover faster after transient errors |
| `max_ban_time_on_fail` | 120s | 60s | Cap ban escalation |
| `SearxEngineAccessDenied` | 180s | 120s | Shorter 403 suspension |
| `SearxEngineTooManyRequests` | 180s | 120s | Shorter 429 suspension |
| `recaptcha_SearxEngineCaptcha` | 604800s (7d) | 3600s (1h) | Don't kill engines for a week |
| `pool_maxsize` | 20 | 50 | More parallel engine requests |
| `http_protocol_version` | 1.0 | 1.1 | Keepalive connections |

Apply with sed on Docker volume mounts (root-owned):
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
  /path/to/searxng/settings.yml
docker restart searxng
```

### Engine Count

Typical SearXNG install: **272 engines total, ~98 enabled**. Verify with:
```bash
curl -s http://localhost:8081/config | python3 -c "
import sys,json; d=json.load(sys.stdin)
enabled = [e['name'] for e in d['engines'] if e.get('enabled')]
print(f'Enabled: {len(enabled)} of {len(d[\"engines\"])}')
"
```

## SearXNG Quirks for Agent Research

This system has SearXNG available via MCP tools (`mcp__searxng__web_search`, `mcp__searxng__web_extract`) AND Firecrawl MCP tools (`mcp__firecrawl__firecrawl_scrape`). The research workflow uses them as complementary layers:

| Phase | Tool | When |
|-------|------|------|
| **Discovery** | `mcp__searxng__web_search` | Free, multi-engine. First pass for finding leads. Pass `context="tech"`/`"news"`/`"scholar"` for category boosting. |
| **Quick extract** | `mcp__searxng__web_extract` | Fast (~15000 chars via Trafilatura), cached 5min. Use for overview pages. |
| **Deep extract** | `mcp__firecrawl__firecrawl_scrape` | Full markdown, proxy support, no char limit. Use for Reddit threads, full articles, JS-rendered content. |
| **Structured extract** | `mcp__firecrawl__firecrawl_scrape` with `formats:["json"]` | LLM extraction into schema from known pages. |

**SearXNG quirks relevant during research:**
- **Name collisions**: Short/generic terms (e.g., "Hermes Agent") collide with unrelated content (HERMES particle physics experiment). Mitigation: add qualifying terms to the query.
- **No site: operator**: SearXNG doesn't proxy `site:github.com` cleanly. Use domain keywords instead.
- **Trafilatura limits**: Strips nav/sidebars, ~15000 char cap. Use Firecrawl for full-page content.
- **Engine silence**: Some queries return only Wikipedia/arXiv results. Add more specific queries to broaden coverage.

## SearXNG Container Operations (Docker)

When SearXNG is unreachable from the bridge (`connection refused`, curl `000`), the usual cause is a container with **no published host port** (`ports={}`) and/or a **non-persistent restart policy** — `docker run` without `-p` and `--restart`. Fix = recreate, preserving the config/data volumes and the ValKey env var (losing them reverts the tuned settings):

```bash
docker rm -f searxng-new
docker run -d --name searxng-new \
  -p 8081:8080 \
  -v /home/sethengine/searxng/config:/etc/searxng \
  -v /home/sethengine/searxng/data:/var/cache/searxng \
  -e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0 \
  --restart unless-stopped \
  searxng/searxng:latest
```

Full verification chain (container → JSON API → bridge stdio → Firecrawl scrape), crash-recovery test, boot-persistence matrix, and user expectations when asked to "bring it up properly and make it stay up": `references/searxng-container-ops.md`.

## Fallback Chain

Always implement a fallback chain — never trust a single backend:

```
SearXNG (primary) → DuckDuckGo (fallback) → Wikipedia (supplement) → arXiv (supplement, auto)
```

**DDG fallback**: scrape `lite.duckduckgo.com` with regex. Free, no API key. Only activate when SearXNG is down.

**Wikipedia supplement**: always add 2-3 results via `en.wikipedia.org/w/api.php`. Lower weight (score 0.6).

**arXiv supplement**: auto-activate for technical queries (keywords: paper, research, model, algorithm, neural, transformer, diffusion, training, benchmark, dataset, architecture, attention, embedding, fine-tun).

## Structured Research Plans (`research_plan` tool)

The `research_plan` tool breaks complex questions into sub-queries, searches each independently, deduplicates across all results, and synthesizes with confidence scores.

### Sub-query derivation

```python
def _derive_subqueries(query, mode="primary"):
    q = query.lower()
    if any(w in q for w in ["vs", "versus", "compare"]):
        # Comparison: one sub-query per entity + head-to-head
        subs.append({"question": f"Reviews and recommendations for {query}", ...})
        subs.append({"question": f"Latest news about {query}", "categories": "news"})
    elif any(w in q for w in ["best", "top", "recommend", "review"]):
        # Recommendations: reviews + news + technical specs
        subs.append({"question": f"Reviews and recommendations for {query}", ...})
        subs.append({"question": f"Latest news about {query}", "categories": "news"})
        subs.append({"question": f"Technical details for {query}", "context": "tech"})
    elif any(w in q for w in ["how to", "tutorial", "guide", "setup"]):
        # Tutorials: guides + common issues
        subs.append({"question": f"Tutorials and guides for {query}", ...})
        subs.append({"question": f"Common issues for {query}", "context": "tech"})
    else:
        # General: overview + news + deep dive
        subs.append({"question": f"What is {query}?", ...})
        subs.append({"question": f"Latest developments in {query}", "categories": "news"})
        subs.append({"question": f"Deep dive into {query}", "context": "tech"})
```

### Confidence scoring

Each result gets a `confidence: N%` derived from:
- **Base score** from the search engine (higher rank = higher base)
- **Category boost** (+0.05 to +0.25) from engine-specific boosts
- **Source diversity** — results from 3+ engines rank higher in synthesis

### Depth modes

| Mode | Sub-queries | Use case |
|------|-------------|----------|
| `quick` | 2 | Straightforward questions, quick overview |
| `standard` | 3-4 | General research (default) |
| `deep` | 5-6 | Complex topics, comprehensive synthesis |

### Output structure

```
# Research Plan: {topic}
## 1. {sub-question}
*Query: `...` | Sources: engine1, engine2*
1. **[Title](url)** *(confidence: 85%)*
   snippet...

## Key Findings (cross-source synthesis)
1. **[Title](url)** — most confident across all sources
```

## Self-Hosted Firecrawl (parallel search + scrape backend)

Self-hosted Firecrawl provides a local alternative to the paid cloud tier. Clone from `github.com/firecrawl/firecrawl`, configure `.env`, run with Docker Compose. 6 containers, ~3-5GB RAM.

### Quick setup (pre-built images — skip BuildKit)

The repo's docker-compose.yaml uses `build:` directives that need Docker BuildKit. If BuildKit is unavailable (Docker 29 on Manjaro ships without `docker-buildx`), switch to pre-built images:

```bash
git clone --depth=1 https://github.com/firecrawl/firecrawl.git ~/firecrawl
cd ~/firecrawl
```

Edit `docker-compose.yaml` — replace three `build:` stanzas with `image:`:
```yaml
x-common-service: &common-service
  image: ghcr.io/firecrawl/firecrawl
  # build: apps/api          ← comment out

playwright-service:
  image: ghcr.io/firecrawl/playwright-service:latest
  # build: apps/playwright-service-ts

nuq-postgres:
  image: ghcr.io/firecrawl/nuq-postgres:latest
  # build: apps/nuq-postgres
```

### .env configuration (minimal working)

```bash
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
BULL_AUTH_KEY=firecrawl-admin-panel

# PostgreSQL — MUST use 'postgres' DB name (pg_cron extension requirement)
POSTGRES_USER=firecrawl
POSTGRES_PASSWORD=firecrawl_pg_secret
POSTGRES_DB=postgres      # NOT a custom name — pg_cron only works in 'postgres' DB

# Resource tuning (adjust per hardware)
NUM_WORKERS_PER_QUEUE=12
CRAWL_CONCURRENT_REQUESTS=20
MAX_CONCURRENT_JOBS=10
BROWSER_POOL_SIZE=8
MAX_CPU=0.85
MAX_RAM=0.85

# AI features — uncomment when local LLM running
# OPENAI_BASE_URL=http://127.0.0.1:8084/v1
# OPENAI_API_KEY=not-needed
```

### SearXNG integration

Firecrawl's `/v1/search` needs a search backend. Default is Google; wire it to SearXNG instead:

```bash
# Firecrawl runs in Docker. To reach SearXNG on host or in another Docker container:
SEARXNG_ENDPOINT=http://host.docker.internal:8081
```

The compose file already has `extra_hosts: ["host.docker.internal:host-gateway"]` — no extra config needed. Verify with: `docker compose logs api | grep "Using searxng search"`.

### Hermes MCP integration

Official npm package `firecrawl-mcp` (v3.22+) supports self-hosted via `FIRECRAWL_API_URL`:

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  firecrawl:
    command: npx
    args: ["-y", "firecrawl-mcp"]
    env:
      FIRECRAWL_API_URL: http://localhost:3002
      # No FIRECRAWL_API_KEY needed for self-hosted
```

Registers ~13 MCP tools: `firecrawl_scrape`, `firecrawl_search`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_interact`, `firecrawl_agent`, `firecrawl_extract`, `firecrawl_batch_scrape`, `firecrawl_monitor_*`, `firecrawl_research_*`.

### Hermes built-in web tools config

Hermes' built-in `web_search` and `web_extract` tools also need to know about the self-hosted Firecrawl instance. Add a `firecrawl:` sub-key under the `web:` section with the API URL:

```yaml
# ~/.hermes/config.yaml
web:
  backend: firecrawl
  search_backend: firecrawl
  extract_backend: firecrawl
  use_gateway: false
  firecrawl:
    FIRECRAWL_API_URL: http://localhost:3002    # Required — without this, web tools fail with "Web tools are not configured"
```

Without this, the built-in tools return: `"Error searching web: Web tools are not configured. Set FIRECRAWL_API_KEY for cloud Firecrawl or set FIRECRAWL_API_URL for a self-hosted Firecrawl instance."`

Both the `web:` section AND the `mcp_servers:` entry are needed for full Hermes integration (MCP tools for agent use, web tools for tool-use). Config changes require a Hermes restart to take effect — `/reload-mcp` only reloads MCP servers, not the `web:` section.

Alternatively, set `FIRECRAWL_API_URL` under the top-level `env:` section in config.yaml — this exports it as a process-wide env var that the web tools also check.

Pitfall: `env.FIRECRAWL_API_URL` must use `localhost` not `127.0.0.1` when Hermes connects through Docker networking or host-loopback that resolves localhost differently.

### API endpoints (v1)

```bash
# Scrape
curl -X POST http://localhost:3002/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","formats":["markdown"]}'

# Search (requires SearXNG or Google config)
curl -X POST http://localhost:3002/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"linux kernel","limit":3,"scrapeOptions":{"formats":["markdown"]}}'

# Crawl
curl -X POST http://localhost:3002/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","limit":5}'

# Map
curl -X POST http://localhost:3002/v1/map \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

All return `{"success": true, "data": {...}}` with markdown content.

### Management script

```bash
# ~/.local/bin/firecrawl-ctl
firecrawl-ctl status   # Container health + API check
firecrawl-ctl up/down  # docker compose up/down
firecrawl-ctl logs     # Tail API logs
firecrawl-ctl pull     # Update pre-built images
```

### Firecrawl-specific pitfalls

- **BuildKit required for source builds**: Docker 29 on Manjaro ships without `docker-buildx`. Install it (`sudo pacman -S docker-buildx`) or use pre-built `ghcr.io/firecrawl/*` images.
- **POSTGRES_DB must be `postgres`**: The nuq-postgres init script calls `CREATE EXTENSION pg_cron` which only works in the `postgres` database. Setting `POSTGRES_DB=firecrawl` (or any non-postgres name) causes the container to crash with "can only create extension in database postgres".
- **host.docker.internal for cross-container access**: When Firecrawl (in Docker) needs to reach SearXNG (on host or in another Docker container), use `host.docker.internal` — not `localhost` or `127.0.0.1`. The compose file already has `extra_hosts: ["host.docker.internal:host-gateway"]`.
- **Supabase/auth warnings are normal**: Self-hosted instances log "bypassing authentication" and "Supabase client not configured" warnings. These are harmless — scraping/crawling works fine without Supabase.

### Caching

TTL-based LRU cache in the bridge process (no Redis/ValKey needed for single-process):

```python
class TTLCache:
    def __init__(self, maxsize=200, ttl=300):
        self._cache = OrderedDict()
        self._ttl = ttl
    
    def get(self, *args, **kwargs):
        k = self._key(*args, **kwargs)
        if k in self._cache:
            val, ts = self._cache[k]
            if time.time() - ts < self._ttl:
                self._cache.move_to_end(k)
                return val
        return None
    
    def set(self, value, *args, **kwargs):
        k = self._key(*args, **kwargs)
        self._cache[k] = (value, time.time())
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

search_cache = TTLCache(maxsize=200, ttl=300)   # 5 min
extract_cache = TTLCache(maxsize=100, ttl=600)  # 10 min
```

**Cache key**: SHA256 of JSON-serialized sorted args+kwargs. Thread-safe via `threading.Lock`.

**ValKey/Redis for SearXNG itself** — install valkey, configure SearXNG to use it:
```yaml
valkey:
  url: valkey://172.17.0.1:6379/0  # Docker bridge IP
```
But this requires Docker container recreation to set `SEARXNG_VALKEY_URL` env var. The in-process cache covers 90% of the benefit with zero infra.

## Fuzzy Deduplication

Character trigram similarity — remove results with >85% title overlap:

```python
def _fuzzy_ratio(a, b):
    a, b = a.lower(), b.lower()
    if a == b: return 1.0
    for sep in (" | ", " - ", " ... ", "..."):
        a = a.split(sep)[0]; b = b.split(sep)[0]
    def trigrams(s): return set(s[i:i+3] for i in range(len(s)-2))
    ta, tb = trigrams(a), trigrams(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0

def deduplicate(results, threshold=0.85):
    deduped, seen = [], []
    for r in results:
        title = r.get("title", "")
        if not any(_fuzzy_ratio(title, s) >= threshold for s in seen):
            deduped.append(r); seen.append(title)
    return deduped
```

## Category-Aware Ranking

Boost specific engines based on query context:

```python
CATEGORY_BOOSTS = {
    "arxiv": 0.15, "github": 0.10, "wikipedia": 0.05, "stackoverflow": 0.08,
    "tech": {"github": 0.20, "stackoverflow": 0.15, "arxiv": 0.15, "wikipedia": 0.10},
    "news": {"reuters": 0.15, "yahoo": 0.10, "wikinews": 0.15},
    "scholar": {"arxiv": 0.25, "semantic scholar": 0.20, "pubmed": 0.20},
}
```

Apply boosts additively, cap at 1.0. Skip dict-type entries when iterating (category sub-maps).

## Pitfalls

- **SearXNG name collisions**: Short/generic search terms collide with unrelated content (e.g., "Hermes Agent" returns HERMES particle physics papers). Always add qualifying terms to disambiguate.
- **3s timeout is the silent killer**: SearXNG default `request_timeout: 3.0` causes many engines to silently time out. Bump to 6.0s.
- **HTTP bridge dies without supervision**: run `--http-port` under systemd or tmux. Don't rely on background shell processes. Use the user service in `templates/mcp-bridge-http.service`.
- **User systemd unit cannot `Requires=docker.service`**: docker.service is a SYSTEM service, invisible from `systemctl --user` — the unit fails to start with "Unit docker.service not found". Drop the `Requires`/`After=docker.service` lines; `Restart=always` (with `StartLimitIntervalSec=0`) already covers the boot race by retrying every 5s until SearXNG is up. Only `network-online.target` is safe to reference in a user unit.
- **Docker volume permissions**: SearXNG config files are owned by `systemd-journal-remote:systemd-journal-remote`. Use sudo or docker exec to edit.
- **llama.cpp proxy toggle**: the "Use llama-server proxy" toggle only appears when EDITING an existing MCP server — not when first adding one. Add the server, save it, then edit to find the toggle.
- **python3 vs python3.14**: Trafilatura may only be installed for a specific Python version. Use explicit path in agent configs when extraction quality matters.
- **Don't scope-creep MCP tools**: when building search bridges for agents, keep tools focused on search. Users explicitly reject kitchen-sink bundles (weather, calculator, currency). Each tool should do one thing well.
- **OpenCode skill discovery ignores symlinks**: skills must be real directories (not symlinks) in `~/.config/opencode/skills/`. Copy with `cp -r`, not `ln -s`.
- **Firecrawl Docker is resource-heavy**: 6 containers use ~3-5GB RAM total. Plan accordingly if memory is constrained. On machines with 32GB+, tune resource limits up in docker-compose.yaml (API to 8 CPUs/16GB, Playwright to 4 CPUs/8GB). Use pre-built `ghcr.io/firecrawl/*` images if BuildKit is unavailable (Docker 29 w/o docker-buildx package).
- **ValKey binding**: default valkey installation binds to 127.0.0.1. Docker containers need the Docker bridge IP (typically 172.17.0.1) or 0.0.0.0 with firewall protection.
- **Recreated containers lose -p and --restart silently**: if someone ran `docker run` without `-p`/`--restart`, SearXNG is unreachable on 8081 and every agent silently falls back to DDG Lite. Container recreation is the fix (must preserve volumes + `SEARXNG_VALKEY_URL` env). See `references/searxng-container-ops.md`.
- **Scope discipline when asked to "make it stay up"**: recreate/diagnose the failing service, but do NOT touch the bridge binary, Hermes config, or Firecrawl unless asked. Verify the whole consumer chain and report explicitly what changed vs. untouched — users get anxious when shared search infra is recreated.

## Quick Deploy

```bash
# Symlink the bridge
ln -sf ~/.config/.src/hermes-stack/mcp-bridge/mcp-bridge ~/.local/bin/mcp-bridge

# Hermes config
hermes mcp add searxng --command ~/.local/bin/mcp-bridge

# OpenCode config (~/.config/opencode/opencode.json)
{"mcp": {"searxng": {"type": "local", "command": ["python3.14", "/home/sethengine/.local/bin/mcp-bridge"], "enabled": true}}}

# llama.cpp WebUI
python3.14 ~/.local/bin/mcp-bridge --http-port 8090
# WebUI: http://127.0.0.1:8090/mcp
```
