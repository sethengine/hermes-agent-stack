# Bridge v4.0.0 — Production Config

## Active deployment (sethengine, 2026-07-12)

### SearXNG
- Docker: `searxng-new` on `:8081`
- Config: `/home/sethengine/searxng/config/settings.yml`
- 98 engines enabled, timeouts tuned (6s request, 3s ban, 50 pool)

### Bridge
- Binary: `/home/sethengine/.local/bin/mcp-bridge`
- Git: `~/.config/.src/hermes-stack/mcp-bridge/`
- HTTP: `:8090/mcp` (python3.14, for llama.cpp WebUI)
- Tools: web_search, web_extract, news_search, scholar_search, research_plan

### Clients
- Hermes: `~/.hermes/config.yaml` → `mcp_servers.searxng`
- OpenCode: `~/.config/opencode/opencode.json` → `mcp.searxng`
- llama.cpp: `http://127.0.0.1:8090/mcp` in WebUI

### ValKey
- Installed (valkey 9.1.0), running, needs sudo to wire to SearXNG
- In-process TTLCache covers 90% of benefit

### Git repos
- `~/.config/.src/hermes-stack/` — full stack (skills, configs, bridge, docs)
- `~/.config/.src/mcp-bridge/` — bridge code only

## Essential Health Checks

```bash
# SearXNG
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/config

# Bridge HTTP
curl -s http://127.0.0.1:8090/mcp | python3 -m json.tool

# Bridge stdio
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' | python3 /home/sethengine/.local/bin/mcp-bridge

# Hermes
hermes mcp test searxng

# ValKey
valkey-cli ping
```

## Restart Procedures

```bash
# Bridge HTTP (needs manual restart — run in tmux or systemd)
python3.14 /home/sethengine/.local/bin/mcp-bridge --http-port 8090

# SearXNG after config changes
sudo sed -i ... /home/sethengine/searxng/config/settings.yml
docker restart searxng-new

# Hermes — new session required after mcp config changes
```
