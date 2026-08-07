---
source: "20260711_184238_43c1f6"
category: software
date: 2026-07-11
tags: [hermes, mcp, profiles, configuration, searxng]
---

# Hermes MCP Profile Configuration

MCP servers in Hermes are configured per-profile. When switching profiles, each needs its own MCP setup for the SearXNG bridge.

## Profile States

- **`default` profile** — Already used the Python bridge (`~/.local/bin/searxng-mcp`)
- **`llama` profile** — Already configured with the Python bridge
- **`new` profile** — Had the broken Docker bridge (`isokoliuk/mcp-searxng`); fixed by switching to the Python bridge

## Fix Pattern

Edit the profile's `config.yaml` (or global config with `--profile` flag):

```yaml
mcp_servers:
  searxng:
    command: python3
    args: ["/home/sethengine/.local/bin/searxng-mcp"]
```

The bridge binary is shared — one file, all profiles.

## References
- [[searxng-python-bridge-http-mode]]
- [[hermes-mcp-search-tools-improvement]]
