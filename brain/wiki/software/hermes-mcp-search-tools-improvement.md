---
source: "20260711_184238_43c1f6"
category: software
date: 2026-07-11
tags: [hermes, mcp, search, searxng, bridge, tools]
---

# Hermes MCP Search Tools Improvement

The SearXNG Python bridge was improved to provide better search tools for agents:

## Original Issues

- Plain text output — agents couldn't parse markdown links
- No content extraction — could search but not fetch pages
- No retry/failover — fragile on network errors
- `number_of_results: 0` edge case caused empty responses

## Improved Tools

1. **`searxng_web_search`** — Returns formatted results with clickable markdown links, engine metadata, scores. Falls back to DuckDuckGo if SearXNG is unavailable.
2. **`searxng_web_extract`** — Direct HTTP fetch + HTML-to-text extraction for fetching page contents.
3. **`news_search`** — SearXNG news category (Google News, Bing News backends).

## Format Fix

Output switched from plain text to markdown link format so agents can follow links without manual URL extraction.

## Key Details

- The bridge binary at `~/.local/bin/searxng-mcp` is shared across all Hermes profiles
- Port 8081 for SearXNG REST API (unchanged)
- The HTTP mode also serves these same tools for llama.cpp WebUI

## References
- [[searxng-python-bridge-http-mode]]
- [[searxng-mcp-bridge-bug]]
