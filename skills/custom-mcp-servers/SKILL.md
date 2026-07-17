---
name: custom-mcp-servers
description: "Build custom Python MCP servers (stdio + StreamableHTTP) for Hermes — authoring, testing, and deploying lightweight bridges that replace broken Docker images or add new capabilities."
version: 1.0.0
platforms: [linux, macos]
---

# Custom MCP Server Authoring

Build lightweight Python MCP stdio servers that Hermes spawns as subprocesses. Use this when:
- A Docker MCP image is broken/unstable (e.g. `isokoliuk/mcp-searxng`)
- You need a bridge to a local service (SearXNG, custom API, database)
- You want zero-dependency servers that don't need npm/docker

## MCP Stdio Transport (Critical)

Hermes communicates with stdio MCP servers via **newline-delimited JSON-RPC**:

```
→ Initialize request (one line, minified JSON)
← Initialize response (one line, minified JSON)
→ notifications/initialized (no response expected)
→ tools/list request
← tools/list response
→ tools/call request
← tools/call response
```

**Key rules from the MCP spec:**
- Messages are delimited by newlines (`\n`)
- Messages **MUST NOT** contain embedded newlines (minified JSON only)
- Server writes responses to stdout, logs to stderr
- JSON-RPC 2.0: every request has an `id`, responses echo that `id`
- `notifications/initialized` is a notification — return `None` (no response)
- Other `notifications/*` — silently drop them

## Skeleton Server

Start with `templates/mcp-server-template.py` — copy and customize.

The skeleton handles:
- JSON-RPC message framing (line-by-line with multi-line fallback)
- `initialize`, `tools/list`, `tools/call`, `ping`, `notifications/*`
- Tool schema definitions
- Error responses

## Tool Response Format

MCP tool results must be wrapped as:
```python
{"content": [{"type": "text", "text": "result string here"}]}
```

**Best practices for agent-friendly output:**
- Use **markdown links**: `[Title](URL)` — agents parse these natively
- Include **metadata**: engine name, score, date for search results
- Keep results **structured** with clear separators between items
- Don't return raw JSON — agents consume text, not structured objects
- Return a meaningful error string (not a stack trace) on failure

## Testing Workflow

### 1. Manual pipe test (fastest iteration)
```bash
# Test initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python3 server.py

# Test tools/list
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 server.py

# Test tools/call
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"my_tool","arguments":{"query":"test"}}}' | python3 server.py
```

### 2. Hermes integration test
```bash
hermes mcp test <server_name>
```
This spawns a real process, runs the MCP handshake, and reports discovered tools. Fast feedback loop before session commit.

### 3. Deploy to Hermes
```bash
hermes mcp remove <name>              # Remove old config if exists
echo "y" | hermes mcp add <name> --command /path/to/server.py
```

### 4. Session restart required
The MCP process for the current session is already running. New or changed servers take effect on next session start (`/new` or restart Hermes). `hermes mcp list` shows the active config but the session holds the old process.

## Dependency Strategy

Prefer **stdlib-only** or **lightweight deps already installed**:
- `json`, `sys`, `urllib.request`, `urllib.error`, `html.parser` — always available
- `httpx` — commonly installed, much better than urllib (keepalive, retries, timeouts)
- Avoid: `aiohttp`, `fastapi`, `flask`, `beautifulsoup4`, `trafilatura` — not guaranteed

### Zero-Dependency HTTP Client Pattern

The safest approach: auto-detect httpx and fall back to urllib. This ensures the bridge
works on ANY Python 3.11+ system regardless of pip packages:

```python
try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
    import urllib.request, urllib.error

def _http_get(url, params=None, timeout=20, headers=None):
    if _HAS_HTTPX:
        return _httpx_get(url, params, timeout, headers)
    return _urllib_get(url, params, timeout, headers)

def _httpx_get(url, params, timeout, headers):
    with httpx.Client(timeout=timeout, headers=headers or {},
                      follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
    return resp

def _urllib_get(url, params, timeout, headers):
    if params:
        url = f"{url}?{urlencode(params)}"
    req = Request(url, headers=headers or {})
    try:
        resp = urlopen(req, timeout=timeout)
        body = resp.read().decode("utf-8", errors="replace")
    except UrllibHTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise _HTTPError(e.code, body) from e
    except URLError as e:
        raise _TimeoutError(str(e)) from e
    resp.text = body
    resp.json = lambda: json.loads(body)
    resp.status_code = resp.status
    return resp

class _HTTPError(Exception):
    def __init__(self, status_code, body):
        self.status_code = status_code; self.body = body
        super().__init__(f"HTTP {status_code}")

class _TimeoutError(Exception):
    pass
```

Then use `_http_get()` throughout instead of direct httpx calls. Wrap calls in
try/except for `_HTTPError` and `_TimeoutError`.

**Why this matters:** The user's `python3` may resolve to different interpreters in different
contexts (Hermes venv vs system vs shell PATH). A hard httpx import fails on systems
where only stdlib is available. The fallback makes the bridge "just work" everywhere.

## Debug Mode

Add a debug toggle via env var:
```python
debug = os.environ.get("SERVER_DEBUG", "").lower() in ("1", "true", "yes")
if debug:
    print(f"[server] message: {msg}", file=sys.stderr)
```

Set temporarily: `SEARXNG_MCP_DEBUG=1 hermes mcp test searxng`

## Dual Transport: Stdio + HTTP

For servers that serve both desktop MCP clients (Hermes, OpenCode — stdio)
and browser-based clients (llama.cpp WebUI — HTTP), add a CLI flag to switch:

```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--http-port", type=int, default=None)
    parser.add_argument("--http-host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    if args.http_port:
        run_http_server(args.http_host, args.http_port)
    else:
        run_stdio()
```

**Key design choices for StreamableHTTP mode:**
- Use Python's stdlib `http.server.BaseHTTPRequestHandler` — no FastAPI/Flask deps
- Handle CORS preflight (OPTIONS) — browsers always send this before POST
- Reject JSON-RPC batch requests per 2025-06-18 spec (return error, don't process)
- Return 202 Accepted for notifications (no body), 200 for responses with JSON body
- Add GET handler for health checks, DELETE for session teardown (no-ops for stateless)
- CORS: `Access-Control-Allow-Origin: *` is sufficient for localhost MCP servers
- `BaseHTTPRequestHandler` uses HTTP/1.0 — fine for short-lived JSON-RPC calls

See `references/searxng-bridge-example.md` for the full implementation.

## llama.cpp WebUI MCP Integration

The llama.cpp bundled WebUI (SvelteKit chat interface at `http://127.0.0.1:8084`)
has a built-in MCP client that runs in the **browser**. It requires HTTP transport
(StreamableHTTP), not stdio.

### Prerequisites
- `llama-server` started with `--jinja` (required for tool calling) and `--ui-mcp-proxy` (enables CORS proxy)
- A tool-calling GGUF model (Qwen3, Devstral, or any model trained for function calls)
- Sufficient context: `-c 16384` minimum (tool schemas + results eat context fast)
- MCP bridge running in HTTP mode on a reachable port

### Setup Steps

1. **Start the bridge in HTTP mode:**
   ```bash
   python3 /path/to/bridge.py --http-port 8090
   ```
   Keep it running — the WebUI connects to it directly for every tool call.

2. **Start llama-server with MCP proxy:**
   ```bash
   llama-server -m model.gguf --jinja --ui-mcp-proxy --port 8084
   ```
   The `--ui-mcp-proxy` flag is mandatory — it enables a CORS proxy endpoint
   that the browser can use to reach MCP servers on other ports.

3. **Add the server in the WebUI:**
   - Open `http://127.0.0.1:8084` → MCP Servers tab → Add New Server
   - **Server URL:** `http://127.0.0.1:8090/mcp`
   - Leave Authorization and Custom Headers empty
   - Hit Save/Add
   - **The connection should work immediately** — CORS headers on the bridge handle it

4. **Proxy toggle (only if needed):**
   - If the direct connection fails with "Failed to fetch (check CORS?)", click **Edit**
     on the saved server and scroll to the bottom of the form
   - Toggle **"Use llama-server proxy"** ON
   - **This toggle ONLY appears in the edit panel, NOT in the add form** — this is a
     known UI quirk in llama.cpp WebUI (mid-2026)
   - The proxy routes requests through `llama-server` (same origin), avoiding CORS entirely

### CORS Behavior
- The bridge sends `Access-Control-Allow-Origin: *` and handles OPTIONS preflight
- Browsers treat cross-port `127.0.0.1` requests as cross-origin
- If the bridge is running and CORS is correct, the direct connection works without the proxy
- 3ms "Failed to fetch" with `"useProxy": false` usually means the bridge process isn't
  running on the target port — check with `curl http://127.0.0.1:8090/mcp` first

## Companion Configuration: Disable Built-in Web Tools

When switching to MCP-based web search (SearXNG), disable the built-in Firecrawl
backend to avoid errors from the cloud service (requires paid subscription):

```yaml
web:
  backend: ''           # disable firecrawl
  search_backend: ''    # no cloud search
  extract_backend: ''   # no cloud extract
  use_gateway: false    # don't proxy through Nous gateway
```

```bash
hermes config set web.use_gateway false
```

The SearXNG MCP tools handle all search/extraction independently — they skip the
`web` config entirely and talk directly to the local SearXNG REST API.

## Cross-Profile MCP Config

Each Hermes profile has its own `config.yaml` with independent `mcp_servers` entries.
When deploying a new MCP bridge, check all active profiles:

```bash
for f in ~/.hermes/profiles/*/config.yaml; do
  echo "=== $f ==="
  grep -A3 "searxng\\|<server_name>" "$f" || echo "(not configured)"
done
```

The bridge binary itself is shared (single file, all profiles reference it), but
the `mcp_servers` entry must exist in each profile that needs the tools. Profiles
using the old Docker bridge need manual migration — replace the `command: docker`
+ `args: [...]` block with `command: /path/to/bridge.py`.

**Non-interactive config update:**
```bash
echo "y" | hermes mcp remove <name> && echo "y" | hermes mcp add <name> --command /path/to/bridge.py
```
The remove+add cycle forces the config to update (direct `config.yaml` edits are blocked
by Hermes security). `echo "y" |` pre-answers both confirmation prompts.

## Multi-Tool Unified Bridge Pattern

Instead of running separate MCP servers per capability, bundle multiple free tools
into a single bridge process. One MCP server entry, all tools available.
This reduces process count and simplifies config.

**Scope depends on user needs.** For search-specific bridges, prefer the `mcp-search-bridge` skill (4 tools: search, extract, news, scholar). The free API services below are general-purpose — only include them if the user explicitly asks.

### Free API Services (no keys needed)

These can be added as MCP tools with zero credential setup:

| Service | API | Tool |
|---------|-----|------|
| Weather | `api.open-meteo.com/v1/forecast` | Current conditions, temp, humidity, wind |
| Currency | `api.frankfurter.app/latest` | Exchange rates, convert between 30+ currencies |
| Geocoding | `geocoding-api.open-meteo.com/v1/search` | City name → lat/lon for weather |
| Time | `zoneinfo` (stdlib) | Current time in any IANA timezone |

**Weather implementation notes:**
- open-meteo is free, no registration, no API key, no rate limits on non-commercial use
- Geocode city names first, then fetch weather by lat/lon
- WMO weather codes map to human-readable descriptions (0=Clear, 61=Light rain, etc.)
- Cache geocoding results to avoid redundant lookups

**Currency implementation notes:**
- frankfurter.app uses ECB rates, updated daily, 30+ currencies
- No API key, no rate limits on reasonable use
- Rate: `GET /latest?amount=100&from=USD&to=EUR` → `{"rates": {"EUR": 92.5}}`

**Safety for calculator tools:**
- Use `eval()` with a restrictive namespace: `{"__builtins__": {}}` + allowed math functions
- Regex-validate input before eval: `r'^[\d\s+\-*/().,%^eπa-z_]+$'`
- Only expose `math.*` functions, `abs`, `round`, `pow` — no `__import__` or `os`

### Bridge file structure

Keep it in one file for zero-install portability:

```
#!/usr/bin/env python3
# ── Config ──
# ── Optional imports (httpx, trafilatura — auto-detect, fall back) ──
# ── HTTP Client (httpx + urllib fallback) ──
# ── Tool implementations (one function per tool) ──
# ── TOOLS list (MCP tool schemas) ──
# ── MCP Handlers (initialize, tools/list, tools/call dispatch) ──
# ── HTTP Transport (BaseHTTPRequestHandler + CORS) ──
# ── main() with argparse (--http-port, defaults to stdio) ──
```

**Scope guidance:** The `mcp-search-bridge` skill covers search-specific bridges (SearXNG, Trafilatura, multi-engine). This general skill covers the MCP protocol skeleton, transport patterns, and agent configs. For a search bridge specifically, prefer `mcp-search-bridge` — it has the search tool scope, pitfall notes, and agent configs already validated.
## General Pitfalls

- **Don't write to stdout except JSON-RPC**: Logging/print statements break the protocol. Use stderr.
- **Handle `notifications/initialized` correctly**: Return `None` (don't write anything). Writing a response to a notification is a protocol error.
- **Echo the request `id` in responses**: Mismatched IDs cause the client to drop responses.
- **Docker `-e` flag requirement**: For Docker-based MCP servers, both `-e VAR` in `args` AND `VAR: val` in `env` config are mandatory. Omitting either means the env var never reaches the container.
- **`hermes mcp test` false negatives**: The test command uses different connection logic than the runtime. A test that says `Connection closed` may still work at runtime. Always verify with a manual pipe test first.
- **Python path mismatch**: The bridge shebang is `#!/usr/bin/env python3`, but `python3` may resolve to different interpreters (Hermes venv, system, pyenv). If the bridge imports httpx but only the venv has it, `ModuleNotFoundError` occurs on system python. Use the zero-dependency fallback pattern to avoid this — never hard-require non-stdlib packages in MCP bridges that users run from terminals.
- **llama.cpp proxy toggle hidden in add form**: The "Use llama-server proxy" toggle only appears when EDITING an existing server, not when first adding one. Users searching for it during initial setup won't find it. Save the server first, then edit it to access the toggle. Also: the toggle is at the bottom of the form, below Custom Headers, requiring a scroll.
- **`127.0.0.1` vs `localhost`**: llama.cpp WebUI users report connections that fail with `localhost` but succeed with `127.0.0.1`. Match the host form consistently — if the WebUI is on `127.0.0.1:8084`, use `127.0.0.1` for the MCP server URL too.

## Reference Files

- `templates/mcp-server-template.py` — Copy-and-customize skeleton for new MCP servers
- `references/searxng-bridge-example.md` — Full annotated example: multi-engine search bridge with dual transport

For search-specific bridges (SearXNG, Trafilatura, DDG fallback), see the `mcp-search-bridge` skill — it has the validated tool scope, pitfall notes, and agent configs.

## Why Docker MCP Bridges Break (MCP Spec)
