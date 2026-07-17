# SearXNG Python MCP Bridge

Replacement for the broken `isokoliuk/mcp-searxng` Docker bridge. A single Python file
using stdlib + `httpx` that talks directly to a local SearXNG REST API (`http://localhost:8081`).

## Why this exists

The Docker bridge broke for two reasons:
1. **MCP spec 2025-06-18**: Removed JSON-RPC batching, changed transport semantics. Old bridge speaks 2024-11-05.
2. **v1.3.1 regression**: Changed default HTTP bind `0.0.0.0` → `127.0.0.1`, breaking Docker Compose.

This bridge bypasses both: it's a direct REST→MCP proxy with no Docker networking, no Node.js,
and implements the 2024-11-05 MCP protocol (which Hermes/OpenCode/llama.cpp WebUI all support).

## Tools provided

| Tool | Description |
|---|---|
| `searxng_web_search` | Search via SearXNG with `query`, `pageno`, `language`, `categories`, `time_range` |
| `searxng_web_extract` | Fetch and extract text content from any URL. Strips HTML to readable text. ~15K char limit. |

## Transport modes

### Stdio (default) — for Hermes, OpenCode, Claude Desktop

No arguments. The bridge reads JSON-RPC from stdin, writes to stdout.

```bash
/home/sethengine/.local/bin/searxng-mcp
```

Hermes config (`~/.hermes/config.yaml`):
```yaml
mcp_servers:
  searxng:
    command: /home/sethengine/.local/bin/searxng-mcp
    enabled: true
```

OpenCode config (`.opencode.json`):
```json
{
  "mcpServers": {
    "searxng": {
      "type": "stdio",
      "command": "/home/sethengine/.local/bin/searxng-mcp"
    }
  }
}
```

### HTTP — for llama.cpp WebUI, browser-based clients

```bash
python3 /home/sethengine/.local/bin/searxng-mcp --http-port 8090
```

Supports CORS (all origins), GET health check at `/mcp`, POST JSON-RPC at `/mcp`.
Rejects JSON-RPC batch requests per 2025-06-18 spec. Notifications return 202 with empty body.

## llama.cpp WebUI setup

### 1. Start the bridge in HTTP mode

```bash
python3 /home/sethengine/.local/bin/searxng-mcp --http-port 8090
```

### 2. Start llama-server with MCP proxy

```bash
llama-server -m /path/to/model.gguf --jinja --ui-mcp-proxy --port 8080
```

`--jinja` is required for tool calling. `--ui-mcp-proxy` enables the CORS proxy
the browser-based WebUI needs to reach MCP servers on different origins.

### 3. Add MCP server in WebUI

Open `http://127.0.0.1:8080`, go to MCP/Tools panel, add a server:

| Field | Value |
|---|---|
| Server URL | `http://127.0.0.1:8090/mcp` |
| Authorization | *(leave empty)* |
| Custom headers | *(leave empty)* |

### 4. Critical: enable proxy toggle

After adding the server, **edit** it (pen icon) and toggle **"Use llama-server proxy" ON**.

This is the #1 gotcha — the proxy toggle only appears in edit mode, not on first add.
**It's also visually hidden below the fold**: scroll down in the edit dialog past
"Custom Headers" to find the toggle at the very bottom. Many users miss it because it
sits outside the visible area of the dialog.

### Common pitfalls

- **Proxy toggle is below the fold in edit dialog**: Scroll past "Server URL", "Authorization", and "Custom Headers" to find the "Use llama-server proxy" switch at the bottom.
- **Use `127.0.0.1` not `localhost`** — browser CORS treats them as different origins
- **3ms "Failed to fetch" = browser blocked, not CORS**: `durationMs` under ~5ms means the browser refused to send the request at all (security policy, not CORS rejection). CORS rejections take 50-200ms because the server responds first. The fix is the proxy toggle.
- **Bridge can work without proxy if CORS is correct**: The bridge sends `Access-Control-Allow-Origin: *` and proper CORS headers. If curl tests pass from the host but the browser blocks it, flip the proxy toggle to route through same-origin.
- **`--webui-mcp-proxy` is deprecated** — use `--ui-mcp-proxy` on newer llama.cpp builds
- **Model must support tool calling** — Qwen2.5/3 7B+, Devstral, or Hermes-style models. Set `-c 16384` for enough context to hold tool schemas + results
- **If nothing happens after a query** — check the WebUI's MCP connection log. "Connection failed" with streamable_http transport usually means the proxy toggle isn't on, or the HTTP bridge isn't running on the port

## Testing the bridge

```bash
# Stdio mode: test with a piped request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | /home/sethengine/.local/bin/searxng-mcp

# HTTP mode: start server, then test
python3 /home/sethengine/.local/bin/searxng-mcp --http-port 8090 &
curl -s http://127.0.0.1:8090/mcp                           # GET health check
curl -s -X POST http://127.0.0.1:8090/mcp                   # POST initialize
  -H "Content-Type: application/json"                       # (same JSON as stdio test)
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize",...}'

# Hermes MCP test
hermes mcp test searxng
```

## Dependencies

- Python 3.11+
- `httpx` (installed system-wide on Manjaro — `python3 -c "import httpx"`)

## Debug mode

```bash
SEARXNG_MCP_DEBUG=1 /home/sethengine/.local/bin/searxng-mcp
```

Logs internal errors and HTTP requests to stderr without breaking the MCP protocol.

## Architecture

```
                         stdio (Hermes/OpenCode)
                              │
SearXNG :8081  ←──  Python bridge  ──→  HTTP :8090 (llama.cpp WebUI)
  (REST API)         (httpx)              (stdlib http.server + CORS)
```

Single process, no containers, no network hops. The bridge calls SearXNG's `/search?format=json`
directly on localhost, strips HTML for `web_extract`, and returns MCP-formatted responses
over whichever transport mode is active.
