---
source_session: 20260521_153915_0b6fa3
date: 2026-05-21
category: software
tags: [hermes, mcp, servers, troubleshooting, context7, c4ai, github]
---

# Hermes MCP Server Troubleshooting

Common root causes for MCP server failures in Hermes:

## context7 (HTTP Transport)

- **Root cause:** URL points to legacy SSE endpoint `/sse`, but Hermes uses streamable HTTP transport by default
- **Fix:** Change URL from `http://localhost:8031/sse` to `http://localhost:8031/mcp`

## github (stdio / Docker)

- **Root cause:** `GITHUB_PERSONAL_ACCESS_TOKEN` set to placeholder `YOUR_GITHUB_PAT_HERE`
- **Fix:** Replace with a real GitHub PAT in `~/.hermes/config.yaml`
- **Diagnostic:** Container exits immediately with "Error: GITHUB_PERSONAL_ACCESS_TOKEN not set"

## c4ai (HTTP Transport)

- **Dual failure mode:** (1) crawl4ai Docker container not running, (2) Hermes default `url` differs from actual server URL
- **Fix:** Ensure Docker container is running, verify URL matches server's advertised endpoint

[[hermes-mcp-config-from-opencode]] [[hermes-agent-config]]
