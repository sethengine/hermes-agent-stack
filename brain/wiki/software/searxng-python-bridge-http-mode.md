---
source: "20260711_184238_43c1f6"
category: software
date: 2026-07-11
tags: [searxng, mcp, bridge, http, llama.cpp, webui]
---

# SearXNG Python Bridge HTTP Mode for llama.cpp WebUI

The SearXNG Python MCP bridge at `~/.local/bin/searxng-mcp` was augmented with an **HTTP/StreamableHTTP transport mode** so it works with llama.cpp WebUI's MCP client (which only supports HTTP transport, not stdio).

## HTTP Mode

```bash
python3 ~/.local/bin/searxng-mcp --http-port 8090
```

The bridge serves MCP over HTTP at `http://127.0.0.1:8090/mcp`. In the WebUI, add a server with:
- **Server URL:** `http://127.0.0.1:8090/mcp`
- Authorization: off
- No custom headers

## Zero-Dependency Fallback

The bridge was hardened to work without `httpx` (missing from system python3) using `urllib.request` as fallback — zero external dependencies.

## Key Details

- The WebUI's "Use llama-server proxy" toggle must be ON when the bridge is behind llama-server; OFF for direct connection
- The HTTP process must stay running (unlike stdio which Hermes manages)
- Systemd user service recommended for persistence: `systemctl --user enable searxng-mcp`

## References
- [[searxng-mcp-bridge-bug]]
- [[hermes-firecrawl-disable-config]]
