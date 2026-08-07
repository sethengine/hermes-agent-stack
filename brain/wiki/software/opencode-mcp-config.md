---
source: "20260711_184238_43c1f6"
date: "2026-07-11"
category: "software"
tags: [opencode, mcp, config, searxng]
wiki-links: [searxng_mcp_bridge_bug, hermes_mcp_config_brave_env_var_fix, hermes_mcp_docker_updates]
---

# OpenCode MCP Configuration

OpenCode was configured to use the unified MCP bridge at `~/.config/opencode/opencode.json`:

```json
{
  "mcpServers": {
    "searxng": {
      "type": "stdio",
      "command": "/home/sethengine/.local/bin/mcp-bridge",
      "args": []
    }
  }
}
```

- Replaced broken Docker-based SearXNG bridge
- `brave-search` disabled (redundant -- the bridge covers it)
- Points to python3.14 for Trafilatura-enhanced extraction
- Same binary as Hermes -- no per-tool setup

**Key:** OpenCode spawns the bridge with whatever `python3` is in its PATH. To use Trafilatura, the bridge's shebang was pointed at python3.14.
