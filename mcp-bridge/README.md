# MCP Bridge

Single-file Python MCP server. 5 search tools, zero API keys.

## Install

```bash
ln -sf ~/.config/.src/hermes-stack/mcp-bridge/mcp-bridge ~/.local/bin/mcp-bridge
```

## Tools

| Tool | Description | Dependencies |
|------|-------------|-------------|
| `web_search` | Federated multi-engine search (SearXNG → DDG → Wikipedia → arXiv) | None |
| `web_extract` | Page extraction (Trafilatura or basic HTML) | trafilatura (optional) |
| `news_search` | Recent news via SearXNG | None |
| `scholar_search` | arXiv paper search | None |
| `research_plan` | Structured multi-query research with synthesis | None |

## Features

- **LRU cache**: 5min TTL for searches, 10min for extracts
- **Fuzzy dedup**: Removes near-duplicates (85% Levenshtein threshold)
- **Category ranking**: Boosts GitHub/arXiv for tech, Reuters for news
- **Resilient**: SearXNG → DuckDuckGo automatic fallback
- **Dual transport**: stdio (Hermes/OpenCode) + HTTP (llama.cpp WebUI)

## Usage

```bash
# stdio mode (Hermes, OpenCode, Claude Desktop)
./mcp-bridge

# HTTP mode (llama.cpp WebUI, browser clients)
python3.14 ./mcp-bridge --http-port 8090
```
