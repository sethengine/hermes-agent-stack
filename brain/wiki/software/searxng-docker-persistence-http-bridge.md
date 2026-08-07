---
source: "20260806_195318_b5a4bd"
category: software
date: 2026-08-06
tags: [searxng, mcp, bridge, docker, systemd, http, persistence, search]
---

# SearXNG Docker Persistence + mcp-bridge Systemd HTTP Service

Fixing SearXNG so the search stack stays up across reboots and other agents can reach it like a real agent, plus wiring the mcp-bridge in persistent HTTP mode.

## SearXNG container was broken (no port publish)

The old `searxng-new` container had **no host port mapping** (`ports={}`) and a `no` restart policy — the bridge targeting `http://localhost:8081` silently fell back to DuckDuckGo Lite. Recreated it with port published and a restart policy:

```bash
docker run -d --name searxng-new \
  -p 8081:8080 \
  -v /home/sethengine/searxng/config:/etc/searxng \
  -v /home/sethengine/searxng/data:/var/cache/searxng \
  -e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0 \
  --restart unless-stopped \
  searxng/searxng:latest
```

- Container listens internally on **8080** (Granian); publish as host `8081→8080`
- Config preserved (timeout 6.0, pool 50) + ValKey cache env intact
- `unless-stopped`: auto-recovers from crashes/daemon restart, **deliberately does NOT** undo a manual `docker stop` (use `docker start searxng-new`)
- SearXNG "Source: duckduckgo" per-result is just which upstream *engine* it fanned out to — `*Sources:* wikipedia` header proves the bridge's primary SearXNG call succeeded (no DDG fallback)

## Persistent HTTP bridge via systemd user service

`~/.config/systemd/user/mcp-bridge-http.service` runs `python3.14 mcp-bridge --http-port 8090`:
- `Restart=always` (every 5s) self-heals and covers the SearXNG ~5–10s boot race
- `enabled` → starts at login/boot
- Note: `Requires=docker.service` breaks startup (Docker is a system service, invisible to user systemd) — use `Restart=always` instead

## HTTP protocol (JSON-RPC 2.0 over POST /mcp)

- `GET /mcp` → `{"server":"research-bridge","version":"4.0.0","tools":[...]}` (CORS `*` wide open)
- `POST /mcp` with `initialize` / `tools/list` / `tools/call {"name":"web_search","arguments":{"query":"..."}}`
- Stateless simplified MCP-HTTP (no session IDs, no SSE). Strict MCP clients need llama-server `--ui-mcp-proxy` toggle or direct JSON-RPC.

## Boot persistence chain

Docker daemon `enabled` → SearXNG+Firecrawl+ValKey auto-restart → agents spawn stdio bridge fresh each launch. Boot race only: first ~5–10s an agent may get DDG fallback once, then self-heals.

## References
- [[searxng_docker]]
- [[searxng_python_bridge_http_mode]]
- [[mcp_bridge_search_tools]]
- [[searxng_mcp_bridge_bug]]
- [[firecrawl_self_hosted_setup]]