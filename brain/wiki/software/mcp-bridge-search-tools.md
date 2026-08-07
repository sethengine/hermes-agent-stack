---
source: "20260711_184238_43c1f6"
date: "2026-07-11"
category: "software"
tags: [mcp, searxng, search, bridge, tools]
wiki-links: [searxng_mcp_bridge_bug, searxng_python_bridge_http_mode, hermes_firecrawl_disable_config, hermes_mcp_search_tools_improvement, hermes_mcp_profile_configuration]
---

# MCP Bridge Search Tools

The unified MCP bridge (`~/.local/bin/mcp-bridge`) was refactored to provide 4 search-only tools, replacing both the Docker-based SearXNG bridge and Firecrawl:

| Tool | Backends | Cost |
|---|---|---|
| `web_search` | SearXNG → DuckDuckGo (fallback) + Wikipedia + arXiv | free |
| `web_extract` | Direct HTTP fetch + HTML strip (Trafilatura on python3.14) | free |
| `news_search` | SearXNG news category (Google News, Bing News) | free |
| `scholar_search` | arXiv API | free |

**Changes applied:**
- Firecrawl fully disabled: `web.backend: ''`, `web.search_backend: ''`, `web.extract_backend: ''`, `use_gateway: false`
- Docker bridge replaced with Python bridge across all 3 Hermes profiles (default, llama, new)
- HTTP mode on `:8090` for llama.cpp WebUI
- `brave-search` disabled in Hermes config (redundant)

The bridge binary (`~/.local/bin/mcp-bridge`) is a single shared file -- no per-profile setup needed.
