# sethengine's agent stack (2026-07-17)

## Services
| Service | Port | Details |
|---|---|---|
| SearXNG | 8081 | Docker, 98 engines, tuned (6s timeout, 50 pool) |
| mcp-bridge HTTP | 8090 | `python3.14 bridge --http-port 8090` |
| mcp-bridge stdio | — | Spawned by Hermes/OpenCode |
| Firecrawl | 3002 | 6-container Docker compose, self-hosted |

## Key configs
- Hermes: `web.backend: firecrawl`, `mcp_servers.searxng: mcp-bridge`
- OpenCode: `command: ["python3.14", "bridge"]`, 119 skills
- Git backup: `~/.config/.src/hermes-stack/`

## Pitfalls
- SearXNG Docker volume owned by root — config edits need sudo
- OpenCode skills must be real dirs, not symlinks
- mcp-bridge HTTP dies on terminal close
- SearXNG needs ~5s after Docker restart
