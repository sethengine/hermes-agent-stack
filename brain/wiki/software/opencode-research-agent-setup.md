---
source_session: 20260603_231307_49f706
date: 2026-06-03
category: software
tags: [opencode, research, agent, mcp]
---

# OpenCode Research Agent Setup

OpenCode has a dedicated `research` agent profile configured for comprehensive internet and git-repo research.

## Configuration

Located at `~/.config/opencode/opencode.json` under the `research` agent profile.

## Tools Enabled

- **searxng** — Free multi-engine web search
- **brave-search** — Brave search API
- **youtube-transcript** — YouTube video transcript extraction
- **playwright** — Full browser automation
- **context7** — Library documentation retrieval
- **c4ai** — Web crawling and content extraction
- **GitHub MCP server** — Repository search, code search, issue tracking

## Research Protocol

The `internet-research` skill (in OpenCode) defines a 7-phase protocol: planning, search, extraction, analysis, synthesis, verification, reporting. This is triggered via the `/research` command.

## Relationship to Hermes

The OpenCode research agent operates independently from Hermes' skill system. There is currently no direct bridge between OpenCode research capabilities and Hermes' brain/wiki knowledge base.

See also: [[research-skill-landscape]], [[git-repo-research-skill]], [[global-session-brain-architecture]]
