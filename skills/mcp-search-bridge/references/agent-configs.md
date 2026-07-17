# MCP Bridge — Agent Configuration Reference

## Hermes (default profile)
```yaml
# ~/.hermes/config.yaml
mcp_servers:
  searxng:
    command: /usr/bin/python3
    args:
      - /home/sethengine/.local/bin/mcp-bridge
    enabled: true
```

## Hermes (other profiles)
Same structure in `~/.hermes/profiles/<name>/config.yaml`.

## OpenCode
```json
{
  "mcpServers": {
    "searxng": {
      "type": "stdio",
      "command": "/home/sethengine/.local/bin/mcp-bridge"
    }
  }
}
```

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
python3 /home/sethengine/.local/bin/mcp-bridge --http-port 8090

# 2. Start llama-server with MCP proxy
llama-server --jinja --ui-mcp-proxy -m /path/to/model.gguf

# 3. WebUI → MCP Servers → Add → URL: http://127.0.0.1:8090/mcp
# 4. Save → Edit → Toggle "Use llama-server proxy" ON
```

## Installation

```bash
# Copy the bridge
cp mcp-bridge ~/.local/bin/mcp-bridge
chmod +x ~/.local/bin/mcp-bridge

# Optional: better extraction
pip install trafilatura --break-system-packages

# Optional: JS-heavy site support
pip install "scrapling[fetchers]" --break-system-packages
scrapling install
```

## Hermes CLI commands

```bash
# Add
echo "y" | hermes mcp add searxng --command /usr/bin/python3 --args /home/sethengine/.local/bin/mcp-bridge

# Remove
echo "y" | hermes mcp remove searxng

# Test
hermes mcp test searxng

# List
hermes mcp list
```

## Disable Firecrawl (use SearXNG instead)

```bash
hermes config set web.backend ''
hermes config set web.use_gateway false
```
