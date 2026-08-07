---
source_session: "20260603_203417_aea2f9"
category: software
tags: [hermes, desktop, artifacts, sessions, outputs]
---

# Hermes Desktop Artifacts Feature

Artifacts is a built-in view in the Hermes Desktop app at `/artifacts` that catalogs outputs the agent generated or referenced across chat sessions.

## What It Collects

The app scans session messages (assistant responses + tool call results) and extracts three kinds:

| Kind | Examples |
|------|----------|
| **Code** | Generated scripts, patches, config files |
| **Images** | Generated or referenced images |
| **Links** | URLs to external resources |

## How It Works

- Automatically populated — no manual tagging
- Runs on the Electron desktop app's built session database
- Provides a gallery/history browser interface to revisit past agent outputs

## Skills in Desktop App

Skills are **not auto-injected** into prompts. The agent: (1) sees available skills via `skills_list` tool (name + description), (2) loads relevant ones with `skill_view()`. Nothing enters the system prompt unless explicitly requested via `--skills` flag.

This means enabling all skills has no prompt overhead — only the tool listing grows.

Related: [[hermes-desktop-font-system]], [[hermes-mcp-server-troubleshooting]], [[hermes-desktop-app-cpu-optimizations]]
