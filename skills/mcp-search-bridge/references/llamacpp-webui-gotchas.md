# llama.cpp WebUI MCP Configuration Gotchas

## CORS Failure Pattern

When adding an HTTP MCP server to llama.cpp WebUI and it fails instantly (3ms):

```
HTTP POST http://127.0.0.1:8090/mcp failed: Failed to fetch (check CORS?)
"durationMs": 3
```

**3ms = browser never sent the request.** Not a server issue. Solutions in order:

1. **Toggle "Use llama-server proxy" ON** — routes through same origin (no CORS needed)
2. Verify bridge is running: `curl -s http://127.0.0.1:8090/mcp`
3. Verify llama-server has `--ui-mcp-proxy` flag

## The proxy toggle is hidden

The "Use llama-server proxy" switch **only appears when EDITING an existing server**, not when first adding one.

Steps:
1. Add server → fill URL → Save
2. Click the pen/edit icon on the saved server
3. Scroll down past Custom Headers — the toggle is at the bottom

## Transport

llama.cpp WebUI only supports HTTP transports (StreamableHTTP, SSE, WebSocket). It does NOT support stdio MCP servers. The bridge must be started in HTTP mode:

```bash
python3 ~/.local/bin/mcp-bridge --http-port 8090
```

## Debug logs

When debugging, check the WebUI's Connection Log (click the "Connection Log (N)" button on the server entry). It shows the full request/response cycle including browser origin, transport type, and whether the proxy was used.
