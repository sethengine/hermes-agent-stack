---
session: 20260502_153854_e0f1a3
date: 2026-05-02
category: software
tags: [searxng, docker, search-engine, setup, troubleshooting]
---

# SearxNG Docker Setup and Troubleshooting

SearxNG running in Docker requires proper volume mounts for `/etc/searxng` (config) and `/var/cache/searxng` (cache). Without volumes, the container runs on baked-in defaults and cannot write settings or cache.

**Correct run command:**
```bash
docker run -d --name searxng --restart unless-stopped \
  -p 8081:8080 \
  -v $(pwd)/searxng/config:/etc/searxng \
  -v $(pwd)/searxng/data:/var/cache/searxng \
  -e SEARXNG_BIND_ADDRESS=0.0.0.0:8080 \
  searxng/searxng:latest
```

**Common issues found with existing container:**
- `chown: /etc/searxng: Read-only file system` → missing config volume mount
- `missing config file: /etc/searxng/limiter.toml` → bot detection disabled by default until configured
- `wikidata engine KeyError: 'name'` → known issue with wikidata.py SPARQL response parsing
- Outdated image (`SearXNG 2025.11.29`) → pulling latest (`2026.5.2`) resolved some issues

The new container auto-creates `settings.yml` from template on first run. Port 8081 was used to avoid conflict with old container on 8080.

## References
