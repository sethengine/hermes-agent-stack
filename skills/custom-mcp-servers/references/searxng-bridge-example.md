# MCP Bridge Reference Implementation — SearXNG + Free Services

Full working example of a custom Python MCP server bridging Hermes to a
local SearXNG instance at `http://localhost:8081`, plus five additional
free services that require zero API keys.

**Why needed:** The official Docker image (`isokoliuk/mcp-searxng`) is
unstable for agent use. This stdio Python bridge replaces it with 7 tools
in a single file.

**Deployed at:** `~/.local/bin/mcp-bridge`  (v1.0.0)
**Hermes config:** `mcp_servers.searxng.command: /home/sethengine/.local/bin/mcp-bridge`
**Former location:** `~/.local/bin/searxng-mcp` (v2.0.1, search+extract only — deprecated)

The bridge auto-detects `httpx` and falls back to stdlib `urllib` — works on ANY
Python 3.11+ regardless of pip packages. Zero external dependencies beyond Python
stdlib. The `#!/usr/bin/env python3` shebang means it works from any shell
regardless of which `python3` is on PATH.

**Profiles configured:** default, llama, new (all three profiles use the same
binary; `new` was migrated from broken Docker bridge to Python bridge).

## Tools Provided (7 total)

### `searxng_web_search`
- Searches local SearXNG via its JSON API (`/search?format=json`)
- Returns 15 results max per page, formatted as markdown with `[title](url)` links
- Metadata: engine name, score, publish date, category
- Supports `categories`, `time_range`, `pageno`, `language`
- 3-retry with 500ms backoff on timeouts

### `searxng_web_extract`
- Fetches any URL and strips HTML to readable text
- Uses stdlib `HTMLParser` (no bs4/trafilatura needed)
- Truncates to ~15K chars with head+tail windows

### `calculator`
- Safe `eval()` with `{"__builtins__": {}}` namespace + math functions
- Regex-validated input: `r'^[\d\s+\-*/().,%^eπa-z_]+$'`
- Supports: sin/cos/tan/sqrt/log/exp/pi/e/ceil/floor/pow/radians/degrees

### `current_time`
- IANA timezone names (`America/New_York`, `Asia/Tokyo`) or abbreviations (EST, PST, JST)
- Abbreviation mapping via common lookup dict → full IANA name → `ZoneInfo`

### `weather` (open-meteo.com, free, no key)
- Geocode city names via `geocoding-api.open-meteo.com/v1/search`
- Fetch current conditions via `api.open-meteo.com/v1/forecast`
- WMO weather codes → human descriptions (0=Clear, 61=Light rain, etc.)
- Returns: temperature, feels-like, humidity, wind speed, conditions

### `currency_convert` (frankfurter.app, free, no key)
- ECB exchange rates, 30+ currencies, updated daily
- `GET /latest?amount=100&from=USD&to=EUR` → `{"rates": {"EUR": 92.5}}`

### `dns_lookup`
- `socket.getaddrinfo()` for A/AAAA records
- Deduplicates and sorts IPs, reports count
- Chrome User-Agent + Accept header, 20s timeout

## Architecture Decisions

### Zero-dependency HTTP client (httpx optional, urllib fallback)
The bridge auto-detects httpx and falls back to stdlib urllib. This ensures
it runs on ANY Python 3.11+ system — Hermes venv, system python, user's shell
PATH — without ModuleNotFoundError. When httpx IS available, it uses connection
pooling and keepalive; when it's not, urllib handles the same GET requests
through a unified `_http_get()` wrapper with `_HTTPError`/`_TimeoutError`
exceptions for unified error handling regardless of transport.

### Markdown output format
Agents parse markdown links natively. The format:
```
1. **[Title](URL)**
   Snippet text...
   *Engine: duckduckgo | Score: 0.95 | Date: 2024-01-15*
```
This lets agents extract URLs for follow-up extraction, track
sources, and cite results — unlike the old plain-text format.

### Separate header configs for search vs extract
Search uses a minimal `User-Agent: Hermes-SearXNG-Bridge/2.0` header.
Extraction uses a full Chrome UA + `Accept: text/html` header to avoid
being blocked by sites that reject bot UAs. Both share the same
`_http_get()` function but pass different header dicts. The unified
client eliminates code duplication — a single retry/timeout/error
path serves both tools.

## SearXNG API Notes

The local SearXNG at `:8081` has 93 enabled engines including:
`arch linux wiki`, `arxiv`, `wikipedia`, `bing images`,
`bing news`, `bing videos`, `duckduckgo`, plus niche engines.

**Result fields available:**
- `url`, `title`, `content` (snippet, ~200-300 chars)
- `engine`, `score`, `category`, `publishedDate`
- `parsed_url`, `img_src`, `thumbnail`, `positions`

**Edge cases:**
- `number_of_results` can be `0` even when results exist — use `or len(results)` fallback
- `answers` field contains instant answers (Wikipedia infoboxes) — display prominently
- `suggestions` field has spelling corrections
- Multiple engines may return the same URL at different ranks

## Config Pattern

```yaml
mcp_servers:
  searxng:
    command: /home/sethengine/.local/bin/searxng-mcp
    # No args, env, or Docker needed — self-contained binary
```

No Docker, no npm, no env vars. Just a Python script on PATH.

## HTTP Transport Implementation

For browser-based MCP clients (llama.cpp WebUI), the bridge also supports
StreamableHTTP via `--http-port`. Implementation uses stdlib `http.server` only.

### Key implementation details

```python
class MCPHTTPHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # CORS preflight — browsers send this before POST
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        # Read JSON-RPC body, pass to handle_request(), return result
        # Reject batch requests (array body) per 2025-06-18 spec
        # Notifications (resp is None) → 202 Accepted, empty body
        # Normal responses → 200, Content-Type: application/json

    def do_GET(self):
        # Health check — returns server info JSON

    def do_DELETE(self):
        # Session termination — no-op in stateless mode, returns 200

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, MCP-Protocol-Version, Mcp-Session-Id, Accept")
```

### CORS gotchas with Python's http.server

- **`BaseHTTPRequestHandler` uses HTTP/1.0 by default** — this is fine for MCP but means
  no keep-alive. Each POST opens a new connection.
- **CORS headers must be on OPTIONS AND the actual response** — browsers check OPTIONS
  for preflight validation, then expect the same headers on the POST response.
- **`Access-Control-Allow-Origin: *`** is sufficient for localhost MCP servers.
  Do NOT use `*` with credentials — MCP doesn't need cookies/sessions for this pattern.
- **`Python 3.11.14`**'s `http.server` works correctly for StreamableHTTP MCP —
  no threading issues with the default `HTTPServer` (single-threaded, but MCP
  requests are short-lived JSON-RPC calls, not long-lived SSE streams).

### CLI interface

```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--http-port", type=int, default=None)
    parser.add_argument("--http-host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    if args.http_port:
        run_http_server(args.http_host, args.http_port)
    else:
        run_stdio()  # default: no args = stdio mode
```

This dual-mode pattern keeps stdio as the zero-arg default (Hermes/OpenCode)
while allowing HTTP mode for browser clients.

## Testing Notes

`hermes mcp test searxng` confirmed: ✓ connected (121ms), ✓ 2 tools
discovered. The remove/re-add cycle (`hermes mcp remove searxng &&
echo "y" | hermes mcp add searxng --command ...`) was needed to update
the config after rewriting the binary. Session restart required for
the new tools to appear in active sessions.
