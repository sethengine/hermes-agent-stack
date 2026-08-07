---
source_session: 20260425_170324_3f10d9
extracted_date: 2026-07-17
category: devops
tags: [hermes, mcp, opencode, configuration, servers]
---

# Converting OpenCode MCP Servers to Hermes Config

OpenCode's `~/.config/opencode/opencode.json` defines MCP servers in JSON. These translate to Hermes `~/.hermes/config.yaml` under the `mcp_servers:` key.

## Transport mapping

| OpenCode | Hermes |
|----------|--------|
| `"type": "stdio"` → `command`/`args`/`env` | Same structure |
| `"type": "http"` → `url` field | Same |

## Config example (stdio)

```yaml
mcp_servers:
  searxng:
    command: docker
    args: [run, -i, --rm, --net=searxng-net, searxng-mcp:latest]
    env:
      SEARXNG_BASE_URL: http://searxng:8888
    enabled: true
```

## Config example (HTTP)

```yaml
  context7:
    url: http://localhost:8031/sse
    enabled: true
```

## Secrets and placeholders

Keys that need real values get placeholders:
- `brave.api_key: "YOUR_BRAVE_API_KEY_HERE"`
- `GITHUB_PERSONAL_ACCESS_TOKEN: "YOUR_GITHUB_PAT_HERE"` (classic PAT with repo scopes)

After filling secrets, run `hermes mcp reload` or restart the CLI. See [[hermes-mcp-server-testing]] for verification.
