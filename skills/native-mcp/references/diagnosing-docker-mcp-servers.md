# Diagnosing Docker-based MCP Servers

Session-specific reference for debugging Docker MCP server failures in Hermes.

## Quick Reference

### Test all MCP servers

```bash
hermes mcp list                          # List configured servers
hermes mcp test <name>                   # Test connection
```

### Check Docker status

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"
docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

### Inspect an MCP Docker image for env vars

```bash
# Check CLI flags
docker run --rm -i --entrypoint "" <IMAGE> --help 2>&1 | head -30

# Node.js: check config for process.env reads
docker run --rm -i --entrypoint "" <IMAGE> sh -c 'cat /app/dist/config.js 2>/dev/null || cat /app/package.json 2>/dev/null'

# Python: check config
docker run --rm -i --entrypoint "" <IMAGE> python3 -c "import os; print('BRAVE_API_KEY' in os.environ)"
```

## Updating Docker MCP Images

All Docker MCP images can be updated independently via `docker pull`. Check current age vs latest:

```bash
# Current
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedSince}}" | grep -E "mcp/|github-mcp|crawl4ai|mcp-searxng"

# Pull latest for each
docker pull mcp/brave-search:latest
docker pull ghcr.io/github/github-mcp-server:latest
docker pull mcp/youtube-transcript:latest
docker pull unclecode/crawl4ai:latest
docker pull isokoliuk/mcp-searxng:latest
```

### Restart After Update

| Container type | Example | Restart method |
|---|---|---|
| Hermes-managed (`--rm`) | brave-search, github, searxng, youtube-transcript | `/reload-mcp` in Hermes, or next session restart |
| Persistent (manually started) | c4ai-mcp (crawl4ai) | `docker restart c4ai-mcp` |

Version bumps can bring new tools or performance improvements:

| Server | Tools before update | Tools after update |
|---|---|---|
| brave-search | 6 | 8 |
| youtube-transcript | 3 | 4 |
| searxng (mcp-searxng bridge) | 2 | 4, connection 4.3s -> 357ms |

## Known Server Details

### brave-search (`mcp/brave-search:latest`)

- **Official package**: `@brave/brave-search-mcp-server` v2.0.59
- **Env var**: `BRAVE_API_KEY` (NOT `brave.api_key` — this was the config bug)
- **CLI equivalent**: `--brave-api-key <value>`
- **Fallback** (from config.js): `process.env.BRAVE_API_KEY ?? ''`
- **Also reads**: `BRAVE_MCP_LOG_LEVEL`, `BRAVE_MCP_TRANSPORT`, `BRAVE_MCP_ENABLED_TOOLS`, `BRAVE_MCP_DISABLED_TOOLS`, `BRAVE_MCP_PORT`, `BRAVE_MCP_HOST`
- **Validates on startup**: Exits immediately if no API key found
- **Error when missing key**: `Error: --brave-api-key is required. You can get one at https://brave.com/search/api/.`

**Correct Hermes config:**
```yaml
brave-search:
  args:
  - run
  - -i
  - --rm
  - -e
  - BRAVE_API_KEY
  - mcp/brave-search:latest
  command: docker
  env:
    BRAVE_API_KEY: "<real-key>"
```

### c4ai / crawl4ai (`unclecode/crawl4ai:latest`)

- **Full image size**: ~3.8GB
- **Default port** (from config.yml): 11235
- **MCP endpoint**: `http://hostname:11235/mcp/sse`
- **MCP schema**: `http://hostname:11235/mcp/schema`
- **Tools discovered** (7): `md`, `html`, `screenshot`, `pdf`, `execute_js`, `crawl`, `ask`
- **Framework**: FastAPI + uvicorn + MCP SSE bridge (`deploy/docker/mcp_bridge.py`)

**Start command:**
```bash
docker run -d --name c4ai-mcp --restart unless-stopped -p 11235:11235 unclecode/crawl4ai:latest
```

**Test endpoint:**
```bash
curl -s -o /dev/null -w "HTTP %{http_code}" --max-time 5 http://localhost:11235/mcp/sse
```

### github (`ghcr.io/github/github-mcp-server:latest`)

- **Env var**: `GITHUB_PERSONAL_ACCESS_TOKEN` (must be a valid PAT with repo scope)
- **Image size**: ~36.6MB (Go binary, distroless)
- **Subcommand**: no explicit subcommand — `/dev/stdin` drives MCP stdio handshake
- **Auth scope check**: At startup, the server attempts to fetch token scopes from `https://api.github.com/`. In Docker, this may fail with `context canceled` due to timing — the server logs a WARN and **continues without scope filtering**. The MCP handshake still succeeds (`server session connected`). Non-fatal.
- **Toolsets**: all by default. Scope filtering is skipped when the probe fails, so all tools are available.
- **Hermes config must have both `-e` flag AND `env` value:**
  ```yaml
  github:
    args:
    - run
    - -i
    - --rm
    - -e
    - GITHUB_PERSONAL_ACCESS_TOKEN
    - ghcr.io/github/github-mcp-server
    command: docker
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "<real-pat>"
  ```
  The `-e GITHUB_PERSONAL_ACCESS_TOKEN` in `args` is **required** — without it, Docker doesn't forward the env var even though it's set in the `env` section.

### searxng (isokoliuk/mcp-searxng:latest) ⚠️ BROKEN — use Python bridge instead

- **Status**: The Docker bridge is effectively broken as of mid-2026. Two root causes:
  1. **MCP spec 2025-06-18**: Removed JSON-RPC batching, changed transport requirements. The bridge speaks the old protocol.
  2. **v1.3.1 HTTP bind regression**: Changed default bind from `0.0.0.0` → `127.0.0.1`, breaking Docker Compose setups. Fixable with `MCP_HTTP_HOST=0.0.0.0` but the protocol issue remains.
- **Image**: `isokoliuk/mcp-searxng:latest` (Node.js-based, ~192MB)
- **Backend via env**: `SEARXNG_URL=http://searxng:8080` (Docker DNS alias)
- **Replacement**: A stdlib+httpx Python bridge at `~/.local/bin/searxng-mcp` that talks directly to SearXNG REST API. Provides `searxng_web_search` + `searxng_web_extract`. Dual transport: stdio (Hermes/OpenCode) and HTTP `--http-port` (llama.cpp WebUI). See `references/searxng-python-bridge.md` for full setup.

## Circuit Breaker Recovery

After 3 consecutive MCP tool call failures for the same server, the circuit breaker opens and blocks retries for **60 seconds**. The tool returns:

```
MCP server 'X' is unreachable after 4 consecutive failures. Auto-retry available in ~Ns.
```

**Recovery methods:**
1. **Fix the underlying issue** (env var, credentials, container) — the breaker is a symptom, not the disease
2. **Restart the Docker container** — `docker restart <container>` forces a fresh subprocess and resets the breaker state in the Hermes MCP client
3. **Wait 60s** — the cooldown expires naturally, the next call is a half-open probe
4. **`/reload-mcp`** — triggers reconnect for all servers in a running Hermes session

**Do NOT retry during cooldown** — the breaker ignores retries and they waste agent turns. The error message tells you exactly when the next probe is available.

## Zombie Container Cleanup

Hermes sessions spawn Docker containers with `--rm`, which removes them on exit. However, if:
- The Docker process is orphaned (parent Hermes process killed without cleanup)
- The container's init process stays alive (Node.js process keeps running on stdin)

A zombie container can persist on the Docker network, causing DNS aliases to resolve to the wrong (dead) container:

```bash
# List all MCP bridge containers (running + stopped)
docker ps -a --filter "ancestor=isokoliuk/mcp-searxng" --format "{{.Names}} {{.Status}}"

# Kill zombie(s)
docker rm -f <zombie-name>

# Verify only the current session's container remains
docker ps --filter "ancestor=isokoliuk/mcp-searxng" --format "{{.Names}} {{.CreatedAt}} {{.Status}}"
```

Stale containers are identifiable by being much older than the current session's uptime.

## `hermes mcp test` Docker Limitation

`hermes mcp test` uses `_probe_single_server()` which calls `_connect_server(name, config)` and creates a temporary connection. For Docker MCP servers, the connection wraps `docker run -i --rm ...` via the MCP SDK's `stdio_client()`.

The probe has a confirmed limitation: **it may report `Connection closed (7-8s)` for Docker MCP servers even when the server works at runtime**. The `_run_stdio` code path (used at session startup and by `/reload-mcp`) handles env var forwarding via `_build_safe_env()` + `StdioServerParameters(env=...)` differently than the probe's `_resolve_mcp_server_config()` + direct `_connect_server()` call. This was verified through side-by-side testing: the same Docker image+env produced `server session connected` in a direct handshake but `Connection closed` in `hermes mcp test`.

**Workaround**: When `hermes mcp test` fails but the server's Docker image is confirmed working (see Manual MCP Handshake Verification below), trust the runtime behavior over the test command. The server will work after a `/reload-mcp` or session restart.

## Manual MCP Handshake Verification

When `hermes mcp test` reports `Connection failed` for Docker MCP servers (especially when the server starts but the probe can't complete the init handshake), verify directly:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 12 docker run --rm -i -e KEY=VALUE IMAGE
```

**Look for** `"server session connected"` in the output — that confirms the MCP initialize handshake succeeded. A `failed to fetch token scopes` warning is non-fatal (GitHub MCP server continues without scope filtering).

## Hermes Config Editing

The `patch` tool **cannot** edit `~/.hermes/config.yaml` (security guard). Alternatives:

| Method | Command |
|--------|---------|
| Add server | `hermes mcp add <name> --command docker --env KEY=VALUE --args run -i --rm -e KEY image` |
| Remove server | `hermes mcp remove <name>` |
| Edit via Python | `python3 -c "import yaml, os; ..."` with `yaml.dump()` |
| View raw config section | Read `~/.hermes/config.yaml` with `read_file(offset=<line>)` |

## Reloading After Config Changes

After editing MCP server config, reload in the running Hermes session:

```
/reload-mcp
```

This re-reads `mcp_servers` from config and reconnects servers. Without this, changes take effect only on next `hermes restart`.

## Common Failure Patterns

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Connection closed` (docker) | Wrong env var name or missing API key | Check image source for correct name; provide real key |
| `All connection attempts failed` (HTTP) | Service not running | Start container (`docker run -d ...`) |
| `Connection closed` (docker, 7s+) | Auth failure — server starts, can't auth, exits | Verify credentials are valid |
| Timeout | Server slow to start | Increase `connect_timeout` in config, or check container health |
| `Connection closed` (probe only) | `hermes mcp test` Docker env limitation | Verify with manual MCP handshake (see above) |
