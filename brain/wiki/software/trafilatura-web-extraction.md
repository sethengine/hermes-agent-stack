---
source: "20260711_184238_43c1f6"
date: "2026-07-11"
category: "software"
tags: [trafilatura, web-extraction, python, mcp]
wiki-links: [searxng_mcp_bridge_bug, hermes_mcp_search_tools_improvement]
---

# Trafilatura Web Extraction

Trafilatura (Python library) was integrated into the MCP bridge's `web_extract` tool for python3.14, providing:

- Metadata extraction (author, date, title)
- Clean markdown output
- Proper boilerplate removal
- Content detection

**Extraction quality by Python version:**

| Version | Quality |
|---|---|
| `python3` (3.11) | Basic HTML stripping |
| `python3.14` | Trafilatura -- metadata, markdown, boilerplate removal |

The HTTP server for llama.cpp WebUI (`:8090`) runs on python3.14. stdio mode (Hermes, OpenCode) uses the active venv python3.

The scrapling fallback code (broken syntax) was removed in favor of clean Trafilatura integration.
