---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

## Diagnosis Workflow

When an MCP server fails to connect, follow this systematic workflow:

### 1. List and test all servers

```bash
hermes mcp list                       # Show all configured servers
hermes mcp test <server_name>         # Test connectivity
```

The test output shows transport type (docker, npx, HTTP) and success/failure. Note the failure mode:
- `Connection closed` — server started but immediately exited (auth/config issue)
- `All connection attempts failed` — nothing is listening (service not running)
- Timeout — server started but slow, or hung

### 2. For Docker-based servers with "Connection closed"

```bash
docker ps --format "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"   # Running containers
docker images | grep <service>                                          # Image exists?
docker ps -a | grep <service>                                           # Stopped containers?
```

Root causes:
- **Container not running**: The image may be pulled but no container is running. Start it with the correct port mapping and env vars.
- **Missing image**: The server image needs to be pulled first (`docker pull <image>`).
- **Auth failure — server starts then exits immediately**: The container has missing or wrong API keys/tokens.

### 3. Verify env var names match what the server expects

Docker MCP images are picky about environment variable names (case-sensitive). The Hermes config passes env vars via `-e <NAME>` in the Docker `args`. Check the image for the exact expected name:

```bash
# Check CLI flags and env var defaults
docker run --rm -i --entrypoint "" <IMAGE> --help 2>&1 | head -30

# For Node.js images, check the source
docker run --rm -i --entrypoint "" <IMAGE> sh -c 'cat /app/dist/config.js 2>/dev/null || cat /app/package.json 2>/dev/null'

# For Go/compiled images, try --help first
docker run --rm -i <IMAGE> --help 2>&1 | head -30
```

Look for `process.env.*` reads or `--option-name` CLI flags. The env var name is **case-sensitive** and must match exactly.

**Known env var gotchas (Docker MCP servers):**
| Server image | Correct env var | Wrong config seen |
|---|---|---|
| `mcp/brave-search` | `BRAVE_API_KEY` | `brave.api_key` |
| `ghcr.io/github/github-mcp-server` | `GITHUB_PERSONAL_ACCESS_TOKEN` | (config is correct) |

### 4. For HTTP SSE servers with "All connection attempts failed"

The HTTP endpoint is not reachable. Check if the service is running:

```bash
# Is the port listening?
ss -tlnp | grep <PORT>

# Does the endpoint respond?
curl -s -o /dev/null -w "HTTP %{http_code}" --max-time 5 http://localhost:<PORT>/<path>

# Check if a container should be running
docker ps -a --format "{{.Names}} {{.Image}}" | grep -i <service>
docker images | grep -i <service>
```

If the image exists but no container is running, start it:

```bash
docker run -d --name <name> --restart unless-stopped -p <PORT>:<PORT> <IMAGE>
```

### 5. Config editing constraint

The `patch` tool cannot modify `~/.hermes/config.yaml` directly (security guard). Use one of these instead:

- **`hermes mcp add` / `hermes mcp remove`** — when adding or removing full server entries
- **`hermes config set mcp_servers.<name>.<key> <value>`** — for simple value changes
- **Python yaml editing** — using `python3 -c "import yaml; ..."` for complex nested changes

After editing, reload MCP servers in the running session with the `/reload-mcp` slash command, or restart Hermes.

## Maintenance

### Circuit Breaker Recovery

After 3 consecutive failures, the MCP circuit breaker opens and blocks retries for **60 seconds**. The tool returns:

```
MCP server 'X' is unreachable after N consecutive failures.
Auto-retry available in ~Ns.
```

**Do NOT retry during the cooldown** — the breaker ignores retries. Instead:
1. Fix the underlying issue (wrong env var, missing container, invalid credentials)
2. Restart the Docker container (`docker restart <name>`) to reset the breaker
3. Or wait 60s for the cooldown to expire naturally
4. The next call after cooldown acts as a half-open probe — on success, the breaker resets

### Docker Image Updates

MCP server images accumulate over time and should be refreshed periodically:

```bash
# Current
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedSince}}" | grep -E "mcp/|github-mcp|crawl4ai"

# Pull latest for each
docker pull mcp/brave-search:latest
docker pull ghcr.io/github/github-mcp-server:latest
docker pull mcp/youtube-transcript:latest
docker pull unclecode/crawl4ai:latest
```
**Note**: `isokoliuk/mcp-searxng` is no longer maintained — use the Python bridge instead (see `references/searxng-python-bridge.md`).

After pulling, restart patterns differ by container type:
- **`--rm` containers** (Hermes-managed via stdio): New image used on next `/reload-mcp` or session restart
- **Persistent containers** (manually started, e.g. `c4ai-mcp`): Must restart explicitly:
  ```bash
  docker restart <container-name>
  ```

Verify with `hermes mcp test <name>` after update. Content updates (new tools, faster connections) often follow version bumps.

---

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.
- **Docker networking**: If using Docker-based MCP servers, containers must be on the same Docker network to resolve each other by hostname. Use `docker network connect --alias <name>` to add DNS aliases. For host access from containers, use `host.docker.internal` (Linux needs `--add-host=host.docker.internal:host-gateway`). **Zombie containers** from dead sessions that stay on the same network can cause DNS confusion — clean them with `docker rm -f <name>`.
- **Env var mismatch**: Docker MCP images expect specific env var names (case-sensitive). Common gotcha: `BRAVE_API_KEY` not `brave.api_key`. Always check the image's source for the exact name (see Diagnosis Workflow §3 and `references/diagnosing-docker-mcp-servers.md` for a table of known mappings).
- **Missing `-e` flag in Docker args**: For Docker-based MCP servers, the `args` list must include `-e ENV_VAR_NAME` for each env var. The `env` config section creates the env var in the subprocess, but Docker needs `-e NAME` in the `args` to forward it into the container. Without it, the env var is set in the parent process but never reaches the Docker container. See `references/diagnosing-docker-mcp-servers.md` for examples.
- **`hermes mcp test` Docker probe limitation**: The test command may report `Connection closed` for Docker MCP servers even when the server works at runtime. The probe doesn't handle Docker env var forwarding identically to `_run_stdio`. Verify with a direct MCP initialize handshake instead — see `references/diagnosing-docker-mcp-servers.md` (Manual MCP Handshake Verification section).
- **Container not running for HTTP/SSE servers**: If the MCP server is configured as an HTTP SSE URL (transport: sse), the backing service must be running and listening. Check with `ss` and `curl`. The image may be pulled but not started.
- **Circuit breaker tripped**: After 3 consecutive failures, the circuit breaker blocks retries for 60s. The tool returns `MCP server 'X' is unreachable after N consecutive failures`. Fix the underlying issue, then `docker restart <container>` resets the breaker state. Do NOT retry during cooldown — waits for the 60s timeout or container restart.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Registers tools like `mcp_time_get_current_time`.

### Filesystem Server (npx)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]

  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Reference Files

- `references/diagnosing-docker-mcp-servers.md` — Session-specific diagnostic details for Docker MCP servers: known env var names, inspect commands, common failure patterns, config editing alternatives.
- `references/searxng-python-bridge.md` — Setup and configuration for the stdlib+httpx SearXNG Python bridge (replaces the broken Docker bridge). Covers stdio mode (Hermes/OpenCode), HTTP mode (llama.cpp WebUI), and llama.cpp WebUI integration gotchas.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)
