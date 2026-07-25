---
name: docker-compose-deployment
description: Deploy self-hosted open-source services via Docker Compose — pre-built image fallback, resource tuning, debugging container crashes, management scripts. Covers the BuildKit workaround, PostgreSQL init pitfalls, and hardware-aware resource limits.
---

# Docker Compose Service Deployment

Deploy complex open-source services (Firecrawl, SearXNG, etc.) via Docker Compose
on a Linux host. Covers common failure patterns and their fixes.

## Prerequisites Check

Always verify before starting:
1. `docker --version && docker compose version` — Docker ≥ 24 recommended
2. `docker info --format '{{.ServerVersion}} running={{.ContainersRunning}}'` — daemon must be running
3. `df -h <target-disk>` — disk space (images can be 500MB–2GB+)
4. `ss -tlnp | grep <port>` — no port conflicts before launch

## Decision: Build vs Pre-built Images

**Always check** `docker-compose.yaml` for both `build:` and commented `image:` lines. Many
open-source projects ship with both options.

**If `docker compose build` fails with `--mount option requires BuildKit`:**
- Check: `docker buildx version` → if "unknown command", BuildKit isn't installed
- Fix: Do NOT try to install `docker-buildx` (requires sudo). Instead, edit
  `docker-compose.yaml` to swap every `build:` for its commented `image:` line.
- Pre-built images live at `ghcr.io/<org>/<service>` or Docker Hub.
- This avoids all compilation (Go, Rust, Node.js toolchains), uses ~10x less time.

Do this for every service: `common-service`, `playwright-service`, `nuq-postgres`, etc.

## Resource Tuning

Default limits in compose files are conservative. Tune to available hardware:

```
Service     Default     This machine (20C/62GB)
─────────────────────────────────────────────
API         4C / 8G     8C / 16G
Playwright  2C / 4G     4C / 8G
```

Also tune these in `.env`:
- `NUM_WORKERS_PER_QUEUE` — roughly cores/2
- `CRAWL_CONCURRENT_REQUESTS` — cores × 1
- `BROWSER_POOL_SIZE` — cores/3
- `MAX_CPU` / `MAX_RAM` — 0.85 (leave headroom for host)

## Debugging Crashed Containers

Containers showing `Exited (N)` after `docker compose up -d`:

```bash
docker compose ps -a                          # see all, including dead
docker compose logs <service> | tail -40      # last 40 lines
docker compose down -v && docker compose up -d  # nuke + restart
```

Common failure modes:

| Symptom | Likely Cause |
|---|---|
| `getaddrinfo ENOTFOUND <hostname>` | That service's container crashed first → other services can't resolve it. Fix the root crash. |
| `CREATE EXTENSION ... ERROR` in Postgres init | Extension requires a specific database name. Check init SQL. |
| `pg_cron` extension fails | Requires `POSTGRES_DB=postgres` (not custom name). Set in `.env`. |
| Warnings about bypassing auth | Normal for self-hosted without Supabase. Ignore. |

## Persistence: restart Policies

Without explicit config, Docker Compose services **do not restart** after a system
reboot. All containers show `Exited (0) N hours ago`.

**Fix:** Add `restart: unless-stopped` to every service in `docker-compose.yaml`:

```yaml
services:
  api:
    restart: unless-stopped       # ← add to each service
    environment: ...
```

Best applied via the YAML anchor when one exists:

```yaml
x-common-service: &common-service
  image: ...
  restart: unless-stopped
```

Then apply:
```bash
docker compose down && docker compose up -d
```

Reboot to verify. All containers should come back with `Up N hours` instead of `Exited`.

## Cross-Container Networking

When two services run in **separate Docker Compose stacks** (different compose
files), they're on different bridge networks and cannot resolve each other by
service name. From container A, reach a service running on the Docker host or
in another stack via `host.docker.internal`:

```yaml
# .env for container A
SOME_ENDPOINT=http://host.docker.internal:8081
```

This requires `extra_hosts` in container A's compose file:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

The `host-gateway` magic resolves to the Docker host's loopback. Works on
Linux with Docker ≥ 20.10. The `host.docker.internal` hostname is only
available **inside** containers, never from the host itself.

## Management Script

Create `bin/<service>-ctl.sh` with `{up,down,restart,status,logs}`:

```bash
#!/bin/bash
set -e
DIR="$HOME/<service>"
case "${1:-status}" in
  up|start)   cd "$DIR" && docker compose up -d ;;
  down|stop)  cd "$DIR" && docker compose down ;;
  restart)    "$0" down && "$0" up ;;
  status|ps)  cd "$DIR" && docker compose ps -a ;;
  logs)       cd "$DIR" && docker compose logs -f --tail=50 "${2:-api}" ;;
  pull)       cd "$DIR" && docker compose pull ;;
  *)          echo "Usage: ..." ;;
esac
```

Symlink to `~/.local/bin/` for PATH access.

## Wiring into Hermes Built-in Tools

When a self-hosted service (like Firecrawl) replaces a cloud provider that Hermes's
built-in tools (web_search, web_extract) expect, you need to set environment variables
that the tool's provider plugin reads.

**How Hermes tools read credentials (two sources, checked in order):**

1. **`hermes_cli.config.get_env_value("VAR_NAME")`** — reads `env:` section of `~/.hermes/config.yaml`
2. **`os.getenv("VAR_NAME")`** — reads OS level environment variables

The provider plugin's `_env_value()` function tries config first, falls back to OS env.
If both return empty, the tool reports "not configured."

**Persistence pattern:**

| Method | File | Scope | Takes effect |
|---|---|---|---|
| Config `.env` | `~/.hermes/config.yaml` → `env:` | Hermes-managed | On agent restart |
| Shell export | `~/.zshenv` (login) + `~/.zshrc` (interactive) | Every zsh process | After new shell/login |

**Verification before user reports it works:**

```bash
python3 -c "
from hermes_cli.config import get_env_value
print('config:', repr(get_env_value('FIRECRAWL_API_URL')))
import os
print('os.env:', repr(os.getenv('FIRECRAWL_API_URL')))
"
```

Both paths must return the value. If only one returns, the tool may still fail
at runtime (config-loading races, tool-gateway path exercises a different code branch).

**Restart requirement:** Adding env vars to `~/.zshrc`/`~/.zshenv` after Hermes is
already running won't be visible until the app restarts or a new shell session opens.

**Firecrawl-specific wiring:**

```yaml
# ~/.hermes/config.yaml
env:
  FIRECRAWL_API_URL: http://127.0.0.1:3002
```

```bash
# ~/.zshenv + ~/.zshrc
export FIRECRAWL_API_URL="http://127.0.0.1:3002"
export FIRECRAWL_API_KEY="self-hosted-no-key-needed"
```

The `FIRECRAWL_API_KEY` can be any non-empty string — self-hosted Firecrawl doesn't
validate it, but the provider plugin's `_get_direct_firecrawl_config()` returns `None`
if both `FIRECRAWL_API_KEY` AND `FIRECRAWL_API_URL` are empty.

## Verification

After containers are healthy:
1. `curl -s http://localhost:<port>/` → should return JSON or HTML (not timeout)
2. Test the core endpoint (scrape, crawl, search, etc.)
3. Check admin panel if one exists
4. `docker compose logs api | grep -iE "(error|fatal)" | grep -v "variable is not"`

## Pitfalls

- **Don't set custom `POSTGRES_DB` unless you've read the init SQL.** Many services
  ship init scripts that hardcode `postgres` or require extensions that only work there.
- **BuildKit is not always available** on Manjaro/Arch Docker packages. The `DOCKER_BUILDKIT=1`
  env var doesn't help — the daemon's compose integration ignores it. Switch to images.
- **`docker compose up -d` may be detected as a long-running server** by agent
  tooling. Run in background mode with `notify_on_complete=true`.
- **Environment variable warnings are normal.** The compose file references many
  optional vars; the "not set" warnings are harmless.

## References

- `references/firecrawl.md` — Firecrawl-specific self-hosting notes
