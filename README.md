# Hermes Stack

AI agent infrastructure — MCP tools, search bridge, agent configs, skills.

```
hermes-stack/
├── README.md
├── docs/
│   └── searxng-mcp-setup.md    # Complete setup guide
├── mcp-bridge/                  # Search + research bridge (zero API keys)
│   ├── README.md
│   ├── mcp-bridge               # v4: 5 tools, cache, dedup, ranking
│   └── searxng-mcp              # v2: legacy fallback
├── configs/
│   ├── hermes/                  # Hermes Agent profile configs
│   │   ├── default-config.yaml
│   │   ├── llama-config.yaml
│   │   └── new-config.yaml
│   ├── opencode/
│   │   └── opencode.json       # OpenCode MCP + providers
│   └── searxng/
│       └── settings.yml         # SearXNG engine config (98 engines, tuned)
└── skills/
    └── last30days/              # Social media research skill
```

## Quick Start

```bash
# Symlink the bridge
ln -sf ~/.config/.src/hermes-stack/mcp-bridge/mcp-bridge ~/.local/bin/mcp-bridge

# Start HTTP server (for llama.cpp WebUI)
python3.14 ~/.local/bin/mcp-bridge --http-port 8090

# Copy configs back (after pulling updates)
cp configs/hermes/default-config.yaml ~/.hermes/config.yaml
cp configs/opencode/opencode.json ~/.config/opencode/opencode.json
```
