---
source: "20260711_184238_43c1f6"
category: software
date: 2026-07-11
tags: [hermes, firecrawl, config, searxng, mcp]
---

# Disabling Firecrawl in Favor of Local SearXNG MCP

Firecrawl requires a paid subscription and errors without one. The solution is to disable it entirely and use the local SearXNG MCP bridge instead.

## Config Change

In `~/.hermes/config.yaml`, set the web section to bypass cloud services:

```yaml
web:
  backend: ''           # no firecrawl
  search_backend: ''    # no cloud search
  extract_backend: ''   # no cloud extract
  use_gateway: false    # don't proxy through Nous gateway
```

## How It Works

The SearXNG MCP tools (`mcp__searxng__searxng_web_search`, `mcp__searxng__searxng_web_extract`) talk directly to SearXNG at `localhost:8081` — no gateway, no firecrawl, no cloud. These are completely separate from the `web.backend` config block.

| System | Config Location | Cost |
|--------|----------------|------|
| Firecrawl (disabled) | `config.yaml` → `web:` | paid subscription |
| SearXNG MCP | `config.yaml` → `mcp_servers.searxng` | free, local |

## References
- [[searxng-python-bridge-http-mode]]
- [[hermes-mcp-search-tools-improvement]]
