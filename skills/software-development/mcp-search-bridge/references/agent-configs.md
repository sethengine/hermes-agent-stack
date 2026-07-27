# MCP Bridge — Agent Configuration Reference

## Hermes (default profile)
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  searxng:
    command: /home/sethengine/.local/bin/mcp-bridge
    enabled: true
```
The bridge has a `#!/usr/bin/env python3` shebang. No explicit python path needed unless you need python3.14 for Trafilatura.

## Hermes (other profiles)
Same structure in `~/.hermes/profiles/<name>/config.yaml`. Sync all profiles:
```bash
echo "y" | hermes mcp remove searxng && echo "y" | hermes mcp add searxng --command /home/sethengine/.local/bin/mcp-bridge
```
**New session required** after mcp config changes — tools won't update in the current session.

## OpenCode
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
**Key**: OpenCode uses `mcp` key (not `mcpServers`). Use `python3.14` explicitly to get Trafilatura extraction quality. The `type: "local"` field is required.

**Skill deployment**: OpenCode discovers skills from `~/.config/opencode/skills/`. Steps:
```bash
# Copy skills (symlinks DON'T work — must be real directories)
cp -r ~/.hermes/skills/<skill-name> ~/.config/opencode/skills/<skill-name>
```
Then restart OpenCode. 119 skills available at `~/.config/opencode/skills/`.

## Claude Desktop
```json
{
  "mcpServers": {
    "searxng": {
      "command": "python3",
      "args": ["/home/sethengine/.local/bin/mcp-bridge"]
    }
  }
}
```

## llama.cpp WebUI
```bash
# 1. Start the bridge in HTTP mode
python3.14 /home/sethengine/.local/bin/mcp-bridge --http-port 8090

# 2. Start llama-server with MCP proxy
llama-server --jinja --ui-mcp-proxy -m /path/to/model.gguf

# 3. WebUI → MCP Servers → Add → URL: http://127.0.0.1:8090/mcp
# 4. Save → Edit → Toggle "Use llama-server proxy" ON
```
Bridge must be running. Use tmux or systemd — background shell processes die with the session.

## Installation

```bash
# Copy the bridge
cp mcp-bridge ~/.local/bin/mcp-bridge
chmod +x ~/.local/bin/mcp-bridge

# Optional: better extraction (python3.14 usually has this)
pip install trafilatura --break-system-packages
```

## Hermes CLI commands

```bash
# Add
echo "y" | hermes mcp add searxng --command /home/sethengine/.local/bin/mcp-bridge

# Remove
echo "y" | hermes mcp remove searxng

# Test
hermes mcp test searxng

# List
hermes mcp list
```

## Firecrawl integration (self-hosted, parallel)
```bash
# Enable Firecrawl for Hermes built-in web tools
hermes config set web.backend firecrawl
hermes config set web.search_backend firecrawl
hermes config set web.extract_backend firecrawl
hermes config set web.use_gateway false
# Set the API URL for self-hosted (no API key needed)
hermes config set env.FIRECRAWL_API_URL http://127.0.0.1:3002
```
Firecrawl doesn't replace mcp-bridge — they serve different purposes. Firecrawl handles Hermes' built-in `web_search`/`web_extract`, mcp-bridge handles MCP tools for all agents. Both can run simultaneously.

## Health checks

```bash
# SearXNG
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/config

# Bridge HTTP
curl -s http://127.0.0.1:8090/mcp | python3 -m json.tool

# Bridge stdio
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' | python3 /home/sethengine/.local/bin/mcp-bridge

# Firecrawl
curl -s -X POST http://127.0.0.1:3002/v0/scrape -H "Content-Type: application/json" -d '{"url":"https://example.com"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('success'))"
```
