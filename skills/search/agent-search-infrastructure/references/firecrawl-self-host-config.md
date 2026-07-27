# Firecrawl Self-Hosted — Working Config (sethengine machine)

Machine: Ultra 7 265K (20C), 62GB RAM, RTX 5060 Ti, Manjaro Linux
SearXNG: Docker container `searxng-new` at host port 8081

## .env (working)

```bash
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
NUM_WORKERS_PER_QUEUE=12
CRAWL_CONCURRENT_REQUESTS=20
MAX_CONCURRENT_JOBS=10
BROWSER_POOL_SIZE=8
BULL_AUTH_KEY=firecrawl-admin-panel
POSTGRES_USER=firecrawl
POSTGRES_PASSWORD=firecrawl_pg_secret
POSTGRES_DB=postgres
MAX_CPU=0.85
MAX_RAM=0.85
ALLOW_LOCAL_WEBHOOKS=true
LOGGING_LEVEL=info
SEARXNG_ENDPOINT=http://host.docker.internal:8081
```

## docker-compose.yaml patches

### Switch to pre-built images (no BuildKit needed)

```yaml
# In x-common-service:
  image: ghcr.io/firecrawl/firecrawl
  # build: apps/api    ← commented out

# In playwright-service:
  image: ghcr.io/firecrawl/playwright-service:latest
  # build: apps/playwright-service-ts

# In nuq-postgres:
  image: ghcr.io/firecrawl/nuq-postgres:latest
  # build: apps/nuq-postgres
```

### Resource tuning (Ultra 7 265K + 62GB)

```yaml
# Playwright service:
  cpus: 4.0    # was 2.0
  mem_limit: 8G # was 4G

# API service:
  cpus: 8.0    # was 4.0
  mem_limit: 16G # was 8G

# MAX_CONCURRENT_PAGES:
  MAX_CONCURRENT_PAGES: ${CRAWL_CONCURRENT_REQUESTS:-20}  # was :-10
```

## Hermes MCP config

```yaml
mcp_servers:
  firecrawl:
    command: npx
    args: ["-y", "firecrawl-mcp"]
    env:
      FIRECRAWL_API_URL: http://localhost:3002
```

## Hermes built-in web tools config

```yaml
web:
  backend: firecrawl
  search_backend: firecrawl
  extract_backend: firecrawl
  use_gateway: false
  firecrawl:
    FIRECRAWL_API_URL: http://localhost:3002
```

Also set in the top-level `env:` section as fallback:
```yaml
env:
  FIRECRAWL_API_URL: http://localhost:3002   # use localhost, not 127.0.0.1
```

Config changes to `web:` section require a full Hermes restart (not just `/reload-mcp`).

## Management script

`~/.local/bin/firecrawl-ctl` — symlinked from `~/firecrawl/bin/firecrawl-ctl.sh`

Commands: `status`, `up`, `down`, `restart`, `logs [svc]`, `pull`, `env`

## Verification

```bash
# Check SearXNG is the search backend
docker compose logs api | grep "Using searxng search"

# Test search
curl -s -X POST http://localhost:3002/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","limit":2}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'results={len(d[\"data\"])}')"

# Test scrape
curl -s -X POST http://localhost:3002/v1/scrape \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","formats":["markdown"]}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'success={d[\"success\"]}')"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| nuq-postgres exits (3) | POSTGRES_DB not 'postgres' | Set POSTGRES_DB=postgres |
| API exits: "getaddrinfo ENOTFOUND nuq-postgres" | nuq-postgres crashed first | Fix nuq-postgres, then docker compose up -d |
| Build fails: "requires BuildKit" | No docker-buildx package | Use pre-built ghcr.io images |
| Search returns empty | SEARXNG_ENDPOINT wrong/unset | Use host.docker.internal:8081 |
| "bypassing authentication" in logs | Normal for self-hosted | Ignore — Supabase not configured |
