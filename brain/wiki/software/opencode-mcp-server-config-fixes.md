---
source_session: "20260521_163423_c00420"
date: 2026-07-24
category: software
tags: [opencode, mcp, searxng, brave-search, github, docker, config, fixes]
wiki-links: [searxng-docker-setup, opencode-mcp-config, hermes-mcp-config-from-opencode, hermes-mcp-server-troubleshooting]
---

# OpenCode MCP Server Config Fixes

Comprehensive fixes applied to a broken OpenCode MCP server configuration:

## SearXNG (3 fixes)
- **DNS resolution**: Container `searxng-new` was NOT on `searxng-net` network. Reconnected and added alias `searxng` so the MCP container resolves `http://searxng:8080`
- **JSON API**: SearXNG `settings.yml` only allowed `html` format — added `json` to formats list, fixing 403 errors
- **Env var placement**: Moved `SEARXNG_URL` from `-e` flag in command array to `environment` dict

## Brave Search
- **Env var name**: Changed `brave.api_key` to `BRAVE_API_KEY` (the Docker image expects the capitalised form)

## GitHub MCP (2 fixes)
- **Token security**: Moved `GITHUB_PERSONAL_ACCESS_TOKEN` from inline command to the `environment` dict
- **Host access**: Added `--add-host=host.docker.internal:host-gateway` for container-to-host git access

## Cleanup Fixes
- Fixed `"lm.studio "` (trailing space) → `"lm.studio"` in provider section
- Added `enabled: true` to `c4ai` and `crawl` MCP servers that were missing it
