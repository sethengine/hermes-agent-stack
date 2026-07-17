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

## Fallback Chain

Always implement a fallback chain — never trust a single backend:

```
SearXNG (primary) → DuckDuckGo (fallback) → Wikipedia (supplement) → arXiv (supplement, auto)
```

**DDG fallback**: scrape `lite.duckduckgo.com` with regex. Free, no API key. Only activate when SearXNG is down.

**Wikipedia supplement**: always add 2-3 results via `en.wikipedia.org/w/api.php`. Lower weight (score 0.6).

**arXiv supplement**: auto-activate for technical queries (keywords: paper, research, model, algorithm, neural, transformer, diffusion, training, benchmark, dataset, architecture, attention, embedding, fine-tun).

## Caching

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

- **3s timeout is the silent killer**: SearXNG default `request_timeout: 3.0` causes many engines to silently time out. Bump to 6.0s.
- **HTTP bridge dies without supervision**: run `--http-port` under systemd or tmux. Don't rely on background shell processes.
- **Docker volume permissions**: SearXNG config files are owned by `systemd-journal-remote:systemd-journal-remote`. Use sudo or docker exec to edit.
- **llama.cpp proxy toggle**: the "Use llama-server proxy" toggle only appears when EDITING an existing MCP server — not when first adding one. Add the server, save it, then edit to find the toggle.
- **python3 vs python3.14**: Trafilatura may only be installed for a specific Python version. Use explicit path in agent configs when extraction quality matters.
- **Don't scope-creep MCP tools**: when building search bridges for agents, keep tools focused on search. Users explicitly reject kitchen-sink bundles (weather, calculator, currency). Each tool should do one thing well.

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
