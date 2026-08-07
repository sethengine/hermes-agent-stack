---
source_session: 20260425_170324_3f10d9
extracted_date: 2026-07-17
category: devops
tags: [hermes, mcp, testing, troubleshooting]
---

# Testing MCP Servers in Hermes Agent

After configuring MCP servers in `~/.hermes/config.yaml`, verify them with the Hermes CLI.

## Commands

```bash
hermes mcp list              # Show all servers and status
hermes mcp test <name>       # Test a single server
hermes mcp reload            # Reload all MCP configs
hermes doctor                # Full health check
```

## Common test results

| Outcome | Meaning |
|---------|---------|
| ✓ Connected + tools | Server running, tools registered |
| ✗ Connection closed | Missing auth key, wrong address, or server not started |
| ✗ Session terminated | HTTP server not listening on that port |
| ✗ All attempts failed | Docker container not built/pulled or port wrong |

## Pitfalls

- **Remote servers** (`url` transport) must be started independently before Hermes connects — `hermes mcp reload` after starting them.
- **Docker stdio servers** need the container image built or pulled first (`docker pull searxng-mcp:latest`).
- **Auth failures** show as "connection closed" — check env vars for correct tokens.
- After changing config, always run `hermes mcp reload` (not just restart).

See [[hermes-mcp-config-from-opencode]] for config setup.
