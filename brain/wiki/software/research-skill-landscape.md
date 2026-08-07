---
source_session: 20260603_231307_49f706
date: 2026-06-03
category: software
tags: [research, skills, landscape, opencode]
---

# Research Skill Landscape

Hermes has multiple research-oriented skills across two platforms:

## Hermes Skills

| Skill | Purpose |
|-------|---------|
| `internet-research` | General web search via searxng, brave-search, multi-engine |
| `research-assistant` | arXiv papers, blog/RSS, LLM wiki, prediction markets |
| `git-repo-research` | Web search + GitHub API for finding/analyzing repos |
| `github-operations` | GitHub CLI/API: PRs, issues, repos, code review |

## OpenCode Research Agent

The `opencode --agent research` config includes: searxng, brave-search, youtube-transcript, playwright, context7, c4ai, crawl, and GitHub MCP server — all wired into a dedicated agent profile with a 7-phase research protocol.

## Gap Analysis

Hermes lacks a unified research orchestrator that can route queries across all these tools. Currently each skill is standalone, and the OpenCode agent operates separately from Hermes' skill system.

See also: [[opencode-research-agent-setup]], [[git-repo-research-skill]], [[global-session-brain-architecture]]
