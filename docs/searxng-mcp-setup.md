# SearXNG MCP Research Bridge — Complete Setup Guide

> Built 2026-07-12 for Hermes Agent, OpenCode, llama.cpp WebUI
> Zero API keys, zero paid services. Replaces Firecrawl, Exa, Brave Search.

---

## Architecture

```
┌─────────────┐    stdio/HTTP     ┌──────────────┐    REST API     ┌──────────┐
│  AI Agent   │ ◄──────────────► │  mcp-bridge   │ ◄────────────► │ SearXNG  │
│  (Hermes,   │                  │  (Python 3.14) │                │ (Docker) │
│  OpenCode,  │                  │                │                │  :8081   │
│  llama.cpp) │                  │  5 tools       │                │          │
└─────────────┘                  │  LRU cache     │                │ 98 free  │
                                 │  fuzzy dedup   │                │ engines  │
                                 │  smart ranking │                │          │
                                 │  :8090 HTTP    │                └──────────┘
                                 └──────┬─────────┘
                                        │ fallback
                                        ▼
                                 ┌──────────────┐     ┌──────────────┐
                                 │ DuckDuckGo   │     │  Wikipedia   │
                                 │ (free, no    │     │  (free API)  │
                                 │  API key)     │     │              │
                                 └──────────────┘     └──────────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │   arXiv      │
                                 │  (free API)  │
                                 └──────────────┘
```

## Tools (v4.0.0)

| Tool | Description | Cache TTL |
|------|-------------|-----------|
| `web_search` | Multi-engine federated search with fuzzy dedup + category-aware ranking | 5 min |
| `web_extract` | Page content extraction via Trafilatura (metadata, markdown) | 10 min |
| `news_search` | Recent news headlines via SearXNG news category | 5 min |
| `scholar_search` | Academic papers via arXiv API | 5 min |
| `research_plan` | Structured multi-query research with cross-source synthesis | — |

### Search flow

1. **SearXNG** (primary) — queries 98 engines including Google, DDG, Brave, Bing, Wikipedia, GitHub
2. **DuckDuckGo** (fallback) — auto-activates if SearXNG is down
3. **Wikipedia** (supplement) — always adds 2-3 relevant articles
4. **arXiv** (supplement) — auto-activates for academic/technical queries
5. **Fuzzy deduplication** — removes near-duplicate results (85% title similarity threshold)
6. **Category-aware ranking** — boosts GitHub/arXiv/StackOverflow for tech queries, Reuters for news

### Cache behavior

```
1st call: web_search("Docker networking") → 2.1s (SearXNG API, fresh)
2nd call: web_search("Docker networking") → <1ms (TTL cache hit, 5min window)

1st call: web_extract("https://example.com") → 1.8s (Trafilatura, fresh)
2nd call: web_extract("https://example.com") → <1ms (TTL cache hit, 10min window)
```

---

## Files

### `/home/sethengine/.local/bin/mcp-bridge`

Single-file Python MCP server. Zero install dependencies — uses stdlib. Optional: `httpx` (faster HTTP), `trafilatura` (better extraction).

**Transport modes:**
- **stdio** (default, no args): Hermes, OpenCode, Claude Desktop
- **`--http-port PORT`**: llama.cpp WebUI, browser-based clients

### `/home/sethengine/.local/bin/searxng-mcp`

Legacy v2 bridge (2 tools). Replaced by `mcp-bridge` v4. Kept as fallback.

### `/home/sethengine/searxng/config/settings.yml`

SearXNG configuration. Key tweaks for agents:

| Setting | Before | After | Reason |
|---------|--------|-------|--------|
| `ban_time_on_fail` | 5s | 3s | Engines recover faster |
| `max_ban_time_on_fail` | 120s | 60s | Shorter max ban |
| `SearxEngineAccessDenied` | 3min | 2min | Shorter 403 suspension |
| `SearxEngineTooManyRequests` | 3min | 2min | Shorter 429 suspension |
| `recaptcha_SearxEngineCaptcha` | 7 days | 1 hour | Don't kill engines for a week |
| `request_timeout` | 3s | 6s | Fewer timeouts (was #1 cause of empty results) |
| `pool_maxsize` | 20 | 50 | More parallel engine requests |
| `http_protocol_version` | 1.0 | 1.1 | Keepalive connections |

---

## Hermes Agent Config

### `~/.hermes/config.yaml`

```yaml
mcp_servers:
  searxng:
    command: /home/sethengine/.local/bin/mcp-bridge
    enabled: true
```

Also updated in profiles: `llama`, `new`

### Web config (Firecrawl disabled)

```yaml
web:
  backend: ''
  search_backend: ''
  extract_backend: ''
  use_gateway: false
```

---

## OpenCode Config

### `~/.config/opencode/opencode.json`

```json
{
  "mcp": {
    "searxng": {
      "type": "local",
      "command": ["python3.14", "/home/sethengine/.local/bin/mcp-bridge"],
      "enabled": true
    }
  }
}
```

Uses `python3.14` explicitly for Trafilatura extraction support.

---

## llama.cpp WebUI Config

### Start bridge

```bash
python3.14 /home/sethengine/.local/bin/mcp-bridge --http-port 8090
```

### Start llama-server

```bash
llama-server \
  -m /path/to/model.gguf \
  --jinja \
  --ui-mcp-proxy \
  --port 8084
```

### WebUI

| Field | Value |
|---|---|
| Server URL | `http://127.0.0.1:8090/mcp` |

---

## ValKey (Redis-compatible cache for SearXNG)

### Install

```bash
sudo pacman -S valkey
sudo systemctl enable --now valkey
```

### Configure (needs sudo)

```bash
sudo tee /etc/valkey/valkey.conf > /dev/null << 'EOF'
bind 0.0.0.0
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
save ""
EOF
sudo systemctl restart valkey
```

### Wire to SearXNG Docker

```bash
docker stop searxng-new && docker rm searxng-new
docker run -d --name searxng-new \
  -p 8081:8080 \
  -v /home/sethengine/searxng/config:/etc/searxng \
  -v /home/sethengine/searxng/data:/var/cache/searxng \
  -e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0 \
  searxng/searxng:latest
```

---

## SearXNG settings changes (2026-07-12)

Apply with sudo (Docker volume owned by root):

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

**Enabled engines** (98 of 272 total): Google, DuckDuckGo, Brave, Bing, Startpage, Wikipedia, GitHub, StackOverflow, YouTube, arXiv, PubMed, PyPI, MDN, Docker Hub, and more.

---

## Version History

| Version | Bridge | Tools | Key Features |
|---------|--------|-------|-------------|
| v1 | `searxng-mcp` (Docker) | 1 | Broken Node.js bridge (isokoliuk/mcp-searxng) |
| v2 | `searxng-mcp` (Python) | 2 | Basic Python bridge, search + extract |
| v2.1 | `searxng-mcp` (Python) | 2 | + HTTP transport for llama.cpp |
| v3 | `mcp-bridge` (Python) | 4 | Multi-engine: SearXNG → DDG → Wikipedia → arXiv |
| v3.1 | `mcp-bridge` (Python) | 4 | Trafilatura extraction (python3.14) |
| v4 | `mcp-bridge` (Python) | 5 | LRU cache, fuzzy dedup, category ranking, research_plan |

---

## Quick Reference

```bash
# Start HTTP bridge (llama.cpp WebUI)
python3.14 /home/sethengine/.local/bin/mcp-bridge --http-port 8090

# Test bridge
hermes mcp test searxng

# Health check
curl http://127.0.0.1:8090/mcp

# Search test
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"test"}}}'

# Research plan test
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"research_plan","arguments":{"query":"Linux kernel security","depth":"quick"}}}'
```
