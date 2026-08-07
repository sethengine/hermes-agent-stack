# SearXNG MCP Bridge Bug

**Source Session:** `20260613_184916_8298ab` (MCP Server Health Check)
**Date:** 2026-07-08
**Category:** software

## Problem

The `isokoliuk/mcp-searxng:v1.11.0` Docker bridge container connects, handles 2 pings via MCP JSON-RPC, then the stdio connection drops. Hermes restarts it every ~3 minutes but it keeps dying. The `hermes mcp test searxng` passes (creates temp connection), but the persistent session pipe dies.

## Root Cause

The bridge uses Node.js `StdioServerTransport` which works for direct MCP call-and-response but **doesn't stay alive** under Hermes' persistent connection model. The connection drops silently after 2 pings.

## Workarounds

1. **Direct API** - SearXNG backend runs on `localhost:8081`, works perfectly via HTTP:
   ```bash
   curl "http://localhost:8081/search?q=query&format=json"
   ```

2. **Python bridge** - A Python-based MCP bridge using HTTP transport (`MCP_HTTP_PORT`) instead of stdio survives the persistent connection.

3. **Skip MCP entirely** - Hermes' built-in `web_search` tool routes through the configured backend (Firecrawl/Brave) and doesn't need the SearXNG bridge.

## For Other Agentic Tools

- **Open WebUI**: Easiest integration - has native SearXNG support
- **llama.cpp server**: Has NO native web search (feature request was closed unimplemented)
- **Claude Code / Codex / Cursor**: Use HTTP API directly or MCP stdio config with the Docker bridge (same stability caveat)
