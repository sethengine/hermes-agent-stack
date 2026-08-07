---
source_session: "20260613_184916_8298ab"
date: 2026-07-07
category: software
tags: [hermes, mcp, docker, containers, updates, maintenance, searxng, brave-search, github]
related: [hermes-mcp-server-troubleshooting, searxng-docker-setup]
---

# Hermes MCP Docker Container Updates

MCP servers running as Docker containers need periodic image updates. Stale images can cause circuit breaker failures and protocol mismatches.

## Update Workflow

```bash
# 1. Pull latest images
docker pull mcp/brave-search
docker pull ghcr.io/github/github-mcp-server
docker pull mcp/youtube-transcript
docker pull unclecode/crawl4ai
docker pull searxng/searxng

# 2. Restart containers to use new images
docker restart hermes-mcp-brave-search
docker restart hermes-mcp-github
docker restart hermes-mcp-youtube
docker restart hermes-mcp-crawl4ai
docker restart hermes-mcp-searxng

# 3. Verify connectivity
# Hermes will reconnect on next tool use — test with any MCP tool call
```

## Why It Matters

- Containers cached for 5-7 months develop stale MCP protocol implementations
- Circuit breakers trip more often on old bridge images
- SearXNG bridge specifically: `ClosedResourceError` on real queries (even when test connects), fixed by restart

## Frequency

Every 1-2 months. Check `docker images` age — any >3 months is worth updating.

## References
- [[hermes-mcp-server-troubleshooting]]
- [[searxng-docker-setup]]
