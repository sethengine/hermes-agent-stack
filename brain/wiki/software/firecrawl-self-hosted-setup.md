---
source: "20260717_202105_87edd9"
date: "2026-07-17"
category: "software"
tags: [firecrawl, self-host, docker, docker-compose, searxng, hermes, mcp, web-search]
wiki-links: [hermes_firecrawl_disable_config, searxng_docker_setup, hermes_mcp_profile_configuration]
---

# Firecrawl Self-Hosted Setup (Docker)

Firecrawl is AGPL-3.0 open source, fully self-hostable via Docker on the same machine as Hermes.

## Prerequisites

- Docker 29.5.1+, Docker Compose 5.1.4+
- Git, ~71 GB free disk, 62 GB RAM (RAM is plentiful on this system)

## Setup

```bash
git clone https://github.com/firecrawl/firecrawl.git
cd firecrawl
# Use pre-built ghcr.io images (avoids BuildKit requirement)
# In docker-compose.yaml, switch API, Playwright, and workers to pre-built image tags
docker compose pull
docker compose up -d
```

**6 containers:** API (port 3002), Playwright service, workers, nuq-postgres (note: DB name `postgres` not `firecrawl` for pg_cron), Redis, Bull queue.

## Hermes Integration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  firecrawl:
    command: npx
    args: ["-y", "firecrawl-mcp"]
    env:
      FIRECRAWL_API_URL: http://localhost:3002
```

Set `FIRECRAWL_API_URL=http://localhost:3002` in `~/.hermes/.env` (Hermes Desktop reads this file at startup — terminal-only `export` does not propagate to the desktop process). Also in `~/.zshenv`, `~/.profile`, and `~/.bashrc` for terminal sessions. Restart Hermes after changing `.env`.

## SearXNG Integration

In Firecrawl's `.env`:
```
SEARXNG_ENDPOINT=http://host.docker.internal:8081
```

Full stack: `Hermes → firecrawl-mcp → Firecrawl API (:3002) → SearXNG (:8081) → web`

## Convenience Commands

Scripted as `firecrawl-ctl`:
- `firecrawl-ctl status` — container health + API check
- `firecrawl-ctl up` / `down` — start/stop
- `firecrawl-ctl logs` — tail all logs

## Related
- [[hermes_firecrawl_disable_config]]
- [[searxng_docker_setup]]
- [[hermes_mcp_profile_configuration]]
