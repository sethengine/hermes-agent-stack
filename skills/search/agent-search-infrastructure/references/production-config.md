# Bridge v4.0.0 — Production Config

## Active deployment (sethengine, 2026-07-17)

### SearXNG
- Docker: `searxng-new` on `:8081`
- Config: `/home/sethengine/searxng/config/settings.yml` (Docker volume, root-owned by `systemd-journal-remote`)
- 98 engines enabled, timeouts tuned (6s request, 3s ban, 50 pool, 1.1 keepalive)
- Engine list: Google, DDG, Brave, Bing, Startpage, Wikipedia, GitHub, StackOverflow, arXiv, and more

### Bridge
- Binary: `/home/sethengine/.local/bin/mcp-bridge`
- Git: `~/.config/.src/hermes-stack/mcp-bridge/mcp-bridge`
- GitHub: https://github.com/sethengine/hermes-agent-stack
- HTTP: `:8090/mcp` (python3.14, for llama.cpp WebUI)
- Tools: web_search, web_extract, news_search, scholar_search, research_plan
- Cache: in-process TTLCache (5min search, 10min extract)
- Dedup: fuzzy title trigram (85% threshold)
- Ranking: category-aware boosts (tech/news/scholar)

### Firecrawl (self-hosted, parallel backend)
- Docker Compose, 6 containers on `:3002`
- API: `/v0/scrape` and `/v0/search` — no auth needed (`TEST_API_KEY` empty)
- Hermes: `FIRECRAWL_API_URL=http://127.0.0.1:3002`
- Resource usage: ~5GB RAM
- Hermes web backend: firecrawl (search + extract + backend)

### Clients

**Hermes** (`~/.hermes/config.yaml`):
```yaml
web:
  backend: firecrawl
  search_backend: firecrawl
  extract_backend: firecrawl
  use_gateway: false
mcp_servers:
  searxng:
    command: /home/sethengine/.local/bin/mcp-bridge
    enabled: true
env:
  FIRECRAWL_API_URL: http://127.0.0.1:3002
```

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
"searxng": {
  "type": "local",
  "command": ["python3.14", "/home/sethengine/.local/bin/mcp-bridge"],
  "enabled": true
}
```

**llama.cpp WebUI**: `http://127.0.0.1:8090/mcp`

### Skills deployed
- 119 skills in OpenCode (`~/.config/opencode/skills/`) — copied from Hermes with `cp -r` (symlinks don't work)
- 119 skills in Hermes (`~/.hermes/skills/`) — auto-discovered
- Includes: deep-research, last30days, internet-research, comfyui, p5js, claude-design, linux-tuning, nvidia-wayland, pipewire, and 100+ more

### ValKey
- Installed (valkey 9.1.0), running at `:6379`
- Config needs sudo: `bind 0.0.0.0`, `maxmemory 256mb`, `maxmemory-policy allkeys-lru`
- SearXNG Docker needs `-e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0` on container recreate
- In-process TTLCache covers 90% of benefit without ValKey

### Git repos
- `~/.config/.src/hermes-stack/` — full stack (skills, configs, bridge, docs), pushed to GitHub
- `~/.config/.src/mcp-bridge/` — bridge code only
- GitHub: https://github.com/sethengine/hermes-agent-stack (909 files, 119 skills, zero secrets)

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

# SearXNG after config changes (Docker volume is root-owned — requires sudo)
sudo sed -i ... /home/sethengine/searxng/config/settings.yml
docker restart searxng-new

# Hermes — new session required after mcp config changes
echo "y" | hermes mcp remove searxng && echo "y" | hermes mcp add searxng --command /home/sethengine/.local/bin/mcp-bridge
```

## Pitfalls discovered this session

- **hermes config set writes in-place but mcp add/remove needs stdin**: Use `echo "y" | hermes mcp remove ...` to auto-approve prompts.
- **SearXNG settings.yml is owned by `systemd-journal-remote`**: Docker volume UID mapping. `patch` tool gets "Permission denied." Use `sudo sed -i` instead.
- **OpenCode symlink gotcha**: Skills as symlinks silently don't load. Must be real directories. Symptom: `ls` shows the directory but OpenCode doesn't list the skill.
- **Bridge HTTP process dies without supervision**: Background shell processes get killed on session end. Use tmux, systemd, or a cron @reboot.
- **ValKey needs sudo for config write**: `/etc/valkey/valkey.conf` requires root. Keep the in-process cache for now.
