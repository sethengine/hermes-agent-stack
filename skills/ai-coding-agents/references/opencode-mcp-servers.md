# OpenCode MCP Server Configuration & Troubleshooting

Docker-based MCP servers under OpenCode need careful networking, environment variable, and config handling. This reference captures the patterns and pitfalls discovered from real debugging sessions.

## OpenCode MCP Config Format

MCP servers live in `~/.config/opencode/opencode.json` under the `"mcp"` key:

```json
{
  "mcp": {
    "server-name": {
      "type": "local",          // "local" = stdio subprocess, "remote" = SSE/WS URL
      "command": ["docker", "run", "-i", "--rm", ...],
      "enabled": true,
      "environment": {           // env vars passed to the subprocess
        "API_KEY": "value"
      }
    },
    "remote-server": {
      "type": "remote",
      "url": "http://localhost:PORT/sse",
      "enabled": true
    }
  }
}
```

Key differences from Hermes MCP config:
- OpenCode uses `command` (array of strings), Hermes uses `command` + `args`
- OpenCode uses `environment` dict for env vars, Hermes uses `env`
- OpenCode has `"type": "local" | "remote"` discriminator
- OpenCode env vars in `command` array with `-e FLAG` are **separate** from `environment` dict

## Critical Pitfall: Env Var Placement

### WRONG — Inline token in command array
```json
"command": ["docker", "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx", "image"]
```
This leaks the token into process args (visible in `ps aux`).

### RIGHT — Pass env var name in command, value in environment dict
```json
"command": ["docker", "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "image"],
"environment": {
  "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
}
```
OpenCode injects `environment` into the subprocess env. The `-e VARNAME` (without `=`) tells Docker to inherit the var from the host process env, which OpenCode sets.

## Docker Networking for MCP Servers

### Pattern: Container-to-Container Communication

When an MCP Docker container needs to reach another container (e.g., SearXNG MCP → SearXNG app):

1. **Create a Docker network** (one-time):
   ```bash
   docker network create searxng-net
   ```

2. **Connect the target service** to the network with a **DNS alias**:
   ```bash
   docker network connect --alias searxng searxng-net searxng-new
   ```
   Without `--alias`, Docker DNS resolves by container name (e.g., `searxng-new`). With alias, it resolves by both the container name AND the alias (e.g., `searxng`).

3. **Run MCP container on same network**:
   ```json
   "command": ["docker", "run", "-i", "--rm", "--network", "searxng-net", ...]
   ```
   The MCP container can now reach `http://searxng:8080`.

### Pitfall: Container NOT on the network
If the target container was started on a different network (e.g., default `bridge`), it won't be reachable by hostname. Check with:
```bash
docker inspect <container> --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
```

If only `bridge` shows up, connect it:
```bash
docker network connect --alias <desired-hostname> <network-name> <container-name>
```

### Pitfall: Container restart drops network connection
`docker restart` preserves network connections. But `docker rm` + `docker run` recreates the container, and you must re-add network aliases. Prefer `docker-compose` for services that need persistent network config.

### Pattern: Container-to-Host Communication

Use `host.docker.internal` or Docker gateway IP:
```json
"command": ["docker", "run", "-i", "--rm", "-e", "API_KEY", "--add-host=host.docker.internal:host-gateway", "image"]
```

On Linux, `host.docker.internal` requires `--add-host` flag or Docker 20.10+ with `extra_hosts` in compose.

## SearXNG-Specific Fixes

### 1. DNS Alias (host resolution)
By default, `docker run --network searxng-net` containers resolve `searxng-new` (the container name), NOT `searxng`. If your config has `SEARXNG_URL=http://searxng:8080`, add the alias:
```bash
docker network connect --alias searxng searxng-net searxng-new
```

### 2. JSON Format Must Be Enabled
SearXNG defaults to HTML-only output. The JSON API returns 403 unless `json` is added to the formats list in settings:
```yaml
# /etc/searxng/settings.yml
search:
  formats:
    - html
    - json      # ← Required for MCP/API access
```
Fix inside container:
```bash
docker exec searxng sed -i '/^    - html$/a\    - json' /etc/searxng/settings.yml
docker restart searxng
```

### 3. Environment in OpenCode Config

The MCP Docker container needs BOTH the `-e VARNAME` flag in the command array AND the value in the `environment` dict. Without `-e VARNAME`, Docker does not inherit the env var from the host process and the container sees it as unset — producing errors like `⚠️ Configuration Issues: SEARXNG_URL not set`.

```json
"searxng": {
  "type": "local",
  "command": [
    "docker", "run", "-i", "--rm",
    "--network", "searxng-net",
    "-e", "SEARXNG_URL",
    "isokoliuk/mcp-searxng:latest"
  ],
  "enabled": true,
  "environment": {
    "SEARXNG_URL": "http://searxng:8080"
  }
}
```

Do NOT put `SEARXNG_URL` as `-e SEARXNG_URL=http://searxng:8080` in the command array (leaks to `ps aux`). Do NOT omit `-e SEARXNG_URL` from the command array (env var won't reach the container). Use the pattern above: flag in command, value in environment dict.

### 3b. Symptom: `SEARXNG_URL not set` Error

If you see `MCP error -32603: ⚠️ Configuration Issues: SEARXNG_URL not set`, it means the `-e SEARXNG_URL` flag is missing from the `command` array. The env var is in `environment` but Docker never receives it because the `-e` flag wasn't passed. Add `"-e", "SEARXNG_URL"` to the command array (without `=value`) and restart OpenCode.

## Common Docker MCP Image Env Var Names

| Image | Required Env Var | Notes |
|-------|-----------------|-------|
| `isokoliuk/mcp-searxng` | `SEARXNG_URL` | Must point to reachable SearXNG instance |
| `mcp/brave-search` | `BRAVE_API_KEY` | NOT `brave.api_key` |
| `ghcr.io/github/github-mcp-server` | `GITHUB_PERSONAL_ACCESS_TOKEN` | PAT with appropriate scopes |
| `mcp/youtube-transcript` | None required | Works out of the box |

## Verifying MCP Server Connectivity

### Stdio (local) servers
These start and wait for JSON-RPC on stdin — they **will time out** if you `docker run` them without input. Test by checking:
1. Docker image exists: `docker image inspect <image>`
2. Container networking: `docker run --rm --network <net> <image>` (will hang — that's OK, means it started)

### Remote (SSE/WS) servers
Check port reachability:
```bash
# Just test if port is open
python3 -c "import socket; s=socket.socket(); s.settimeout(2); print('OK' if s.connect_ex(('localhost', PORT))==0 else 'FAIL'); s.close()"
```
Don't use `curl` on SSE endpoints — they stream forever and hang.

### SearXNG functional test
```bash
curl "http://localhost:8081/search?q=test&format=json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"results\"])} results')"
```

## JSON Config Pitfall: Trailing Spaces

Provider keys with trailing spaces silently break model resolution:
```json
// WRONG — "lm.studio " won't match any model
"lm.studio ": { ... }

// RIGHT
"lm.studio": { ... }
```

JSON doesn't strip whitespace in keys. Validate with `python3 -c "import json; json.load(open('opencode.json'))"`.

## Agent Tool Permission Flags

In `opencode.json`, agent configs have a `tools` dict that can enable/disable MCP servers per agent:
```json
"agent": {
  "power": {
    "tools": {
      "searxng": true,
      "context7": true,
      "brave-search": true,
      "youtube-transcript": true,
      "crawl": true,
      "c4ai": true,
      "playwright": true,
      "github": true
    },
    "mode": "all"
  },
  "simple": {
    "tools": {
      "searxng": true,
      "playwright": false,
      "github": false
    },
    "mode": "all"
  }
}
```
The tool names here must match the MCP server keys exactly. Missing or misspelled keys default to disabled.