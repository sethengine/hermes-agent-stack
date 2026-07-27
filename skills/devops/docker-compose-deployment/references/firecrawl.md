# Firecrawl Self-Hosting Reference

## Repo
`https://github.com/firecrawl/firecrawl` — AGPL-3.0, 152k stars

## What You Get (Self-Hosted vs Cloud)

| Feature | Self-Hosted | Cloud |
|---|---|---|
| `/scrape` — URL → markdown/HTML/screenshot | ✅ | ✅ |
| `/crawl` — crawl entire site | ✅ | ✅ |
| `/map` — discover all URLs | ✅ | ✅ |
| `/search` — web search + page content | ✅ (needs Google/SearXNG) | ✅ |
| `/batch/scrape` — async bulk | ✅ | ✅ |
| `/extract` — structured data (AI) | ✅ (needs LLM key) | ✅ |
| Fire-engine (anti-bot proxies) | ❌ | ✅ |
| API key required | ❌ (optional) | ✅ |

## Container Stack (6 containers)

```
redis:alpine          — job queue backend
rabbitmq:3-management — message broker
nuq-postgres (custom) — PostgreSQL + pg_cron + pgvector
playwright-service    — JS rendering (Chromium)
foundationdb          — experimental queue backend (disabled by default)
firecrawl (API)       — main API + workers (harness.js manages sub-processes)
```

## Critical Configuration

### `.env` essentials

```
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false        # no Supabase in self-hosted
BULL_AUTH_KEY=firecrawl-admin-panel  # admin UI access key
POSTGRES_DB=postgres               # MUST be 'postgres' — pg_cron requires it
```

### pg_cron pitfall

The nuq-postgres init script runs `CREATE EXTENSION IF NOT EXISTS pg_cron`. This
extension **only works in the `postgres` database**. If you set `POSTGRES_DB=firecrawl`
(or any custom name), the container exits with code 3:

```
ERROR: can only create extension in database postgres
DETAIL: Jobs must be scheduled from the database configured in cron.database_name
```

Fix: `POSTGRES_DB=postgres` in `.env`.

### AI Features (LLM Integration)

Firecrawl supports OpenAI-compatible APIs for `/extract` and JSON-format scraping.
When the local LLM server is running at `127.0.0.1:8084` (llama.cpp with
Qwythos-9B-v2-MTP-Q8_0), uncomment in `.env`:

```
OPENAI_BASE_URL=http://127.0.0.1:8084/v1
OPENAI_API_KEY=not-needed
MODEL_NAME=qwythos-9b
```

### Search Backend

Without `SEARXNG_ENDPOINT`, Firecrawl uses Google search directly. When SearXNG
is running:

**Same compose file (single stack):** Use the container hostname:
```yaml
SEARXNG_ENDPOINT=http://searxng:8080
```

**Separate Docker stacks (Firecrawl + SearXNG in different compose files):**
Use `host.docker.internal` (requires `extra_hosts` in docker-compose.yaml):
```yaml
SEARXNG_ENDPOINT=http://host.docker.internal:8081
```

Verify in logs:
```bash
docker compose logs api | grep "Using searxng search"
```

If the search endpoint returns `SCRAPE_SITEMAP_ERROR` or sitemap 404s,
those are normal for sites without sitemaps — the underlying search still works.

## Resource Tuning for This Machine

Hardware: Ultra 7 265K (20C/20T) + 62GB RAM + RTX 5060 Ti

docker-compose.yaml changes:
- `playwright-service`: 4 CPUs / 8GB (default: 2/4)
- `api`: 8 CPUs / 16GB (default: 4/8)

.env changes:
- `NUM_WORKERS_PER_QUEUE=12` (default: 8)
- `CRAWL_CONCURRENT_REQUESTS=20` (default: 10)
- `MAX_CONCURRENT_JOBS=10` (default: 5)
- `BROWSER_POOL_SIZE=8` (default: 5)

## Expected Warnings (harmless)

| Warning | Why |
|---|---|
| "You're bypassing authentication" | No Supabase configured. Normal. |
| "Supabase client is not configured" | Self-hosted doesn't support Supabase. Ignore. |
| "Results might differ from cloud offering" | Map endpoint uses different backend. |
| "Sitemap not found" | Site has no sitemap.xml. Normal for many sites. |

## Management

`firecrawl-ctl` script at `~/.local/bin/firecrawl-ctl`:

```
firecrawl-ctl status    — all containers + API health
firecrawl-ctl up/down   — start/stop
firecrawl-ctl logs      — tail API logs
firecrawl-ctl pull      — update pre-built images
```

Admin panel: `http://localhost:3002/admin/firecrawl-admin-panel/queues`

## Quick API Test

```bash
# Scrape
curl -X POST http://localhost:3002/v1/scrape \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","formats":["markdown"]}'

# Crawl
curl -X POST http://localhost:3002/v1/crawl \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","limit":5}'

# Map
curl -X POST http://localhost:3002/v1/map \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

## File Locations

```
~/firecrawl/                          — repo root
~/firecrawl/.env                      — configuration
~/firecrawl/docker-compose.yaml       — resource limits tuned
~/firecrawl/bin/firecrawl-ctl.sh      — management script
~/.local/bin/firecrawl-ctl            — symlink to script
```

## Hermes Integration

To make Hermes's built-in `web_search` and `web_extract` tools use the local
Firecrawl instance instead of erroring with "Web tools are not configured":

**1. `~/.hermes/.env` file (recommended — persists across restarts):**
```bash
FIRECRAWL_API_URL=http://127.0.0.1:3002
```

**2. config.yaml `env:` section (Hermes-managed):**
```yaml
env:
  FIRECRAWL_API_URL: http://127.0.0.1:3002
```

**3. `web:` section (informs the web_search tool's backend selector):**
```yaml
web:
  backend: firecrawl
  use_gateway: false
```

**4. Shell exports (for all zsh sessions — ensures os.getenv() has it):**
```bash
# ~/.zshenv
export FIRECRAWL_API_URL="http://127.0.0.1:3002"
export FIRECRAWL_API_KEY="self-hosted-no-key-needed"
```

**5. Restart Hermes** — env vars are loaded at process start.

**Why both?** The Firecrawl provider's `_env_value()` tries `hermes_cli.config.get_env_value()`
first (reads config.yaml), falls back to `os.getenv()`. Having both paths set avoids
config-loading races. The `FIRECRAWL_API_KEY` can be any string — self-hosted Firecrawl
doesn't validate it, but `_get_direct_firecrawl_config()` returns `None` if BOTH
`FIRECRAWL_API_KEY` and `FIRECRAWL_API_URL` are empty.

**Verification:**
```bash
python3 -c "
from hermes_cli.config import get_env_value
print('config:', repr(get_env_value('FIRECRAWL_API_URL')))
import os
print('os.env:', repr(os.getenv('FIRECRAWL_API_URL')))
from hermes_cli.config import load_config
print('web config:', load_config().get('web', {}))
"
```

Both config and os.env paths must show the URL. The `web.backend` should be `firecrawl`.
