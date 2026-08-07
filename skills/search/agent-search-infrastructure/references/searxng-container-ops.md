# SearXNG Container Operations — bring it up, keep it up, verify it works for consumers

Session lesson: a `searxng` container silently deployed with **no `-p` host port**
and **no `--restart`** policy caused every agent to fall back to DuckDuckGo Lite.
Users notice this only when the bridge log shows `Source: duckduckgo` or the API
returns `000` (connection refused). Fix is container recreation, then verify the
WHOLE consumer chain — not just the container.

## Root cause (this system)

`docker inspect searxng-new` showed:

- `ports={}` → host port 8081 was never published (container listens on 8080 internally, Granian)
- restart policy `no` → died and never came back

Both must be fixed at `docker run` time; they cannot be patched onto a live container.

## Correct container (volumes + env preserved)

```bash
docker rm -f searxng-new
docker run -d --name searxng-new \
  -p 8081:8080 \
  -v /home/sethengine/searxng/config:/etc/searxng \
  -v /home/sethengine/searxng/data:/var/cache/searxng \
  -e SEARXNG_VALKEY_URL=valkey://172.17.0.1:6379/0 \
  --restart unless-stopped \
  searxng/searxng:latest
```

Preserve the two volumes and `SEARXNG_VALKEY_URL` or the tuned settings
(`request_timeout: 6.0`, `pool_maxsize: 50`, bans) are silently reverted to stock.

## Verification chain (run ALL of these)

1. **Container state + port + policy:**
   ```bash
   docker inspect searxng-new --format 'state={{.State.Status}} restart={{.HostConfig.RestartPolicy.Name}} port={{json .NetworkSettings.Ports}}'
   ```
   Expect `state=running restart=unless-stopped` and a `8081` host port mapping.

2. **HTTP reachable:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8081/search?q=test&format=json"   # → 200
   ```

3. **Bridge end-to-end, exactly how an agent spawns it (stdio):**
   ```bash
   printf '%s\n%s\n' \
     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
     '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"linux kernel"}}}' \
     | timeout 25 python3 ~/.local/bin/mcp-bridge 2>/dev/null
   ```
   Expect real ranked results + `Sources:`. If it shows `Source: duckduckgo`, the
   bridge just proved SearXNG is unreachable — don't call it fixed.

4. **Firecrawl unaffected (containers up ≠ working):**
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/            # → 200
   curl -s -X POST http://localhost:3002/v0/scrape -H "Content-Type: application/json" \
     -d '{"url":"https://example.com"}'                                         # success:true, has markdown
   ```
   Firecrawl stack (check `docker inspect firecrawl-api-1 ... Label com.docker.compose.project.config_files`):
   `firecrawl-api-1`, `firecrawl-nuq-postgres-1`, `firecrawl-redis-1`, `firecrawl-rabbitmq-1`, `firecrawl-playwright-service-1`.

## Crash-recovery proof

`unless-stopped` must survive a SIGKILL (recreates the container), not just a graceful stop:

```bash
sudo kill -9 "$(docker inspect searxng-new --format '{{.State.Pid}}')"
sleep 8
docker inspect searxng-new --format '{{.State.Status}}'       # → running
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081/config   # → 200
```

## Boot persistence matrix (verified on this box)

| Service | Mechanism | Check |
|---|---|---|
| Docker daemon | systemd | `systemctl is-enabled docker` → `enabled` |
| containerd | bundled with dockerd | often `disabled` — normal, don't chase it |
| ValKey (SearXNG cache) | systemd | `systemctl is-enabled valkey` → `enabled` |
| SearXNG | `restart=unless-stopped` | restarts when Docker starts |
| Firecrawl (5-6 containers) | compose `restart: always` (line 23/60 in `~/firecrawl/docker-compose.yaml`) | restarts with Docker; even overrides manual `stop` |
| Bridge stdio | spawned per-agent at launch | no service needed — always fresh |

**Boot race:** Docker starts → SearXNG needs a few extra seconds; Firecrawl's whole
stack (postgres→redis→rabbitmq→API) takes longer. For the first few seconds an agent
query falls back to DDG Lite, then self-heals. Not a failure; don't over-fix.

**Manual `stop` semantics:** `unless-stopped` deliberately does NOT restart a container
you manually `docker stop` (you asked for it stopped). It only restarts on crash/daemon/
reboot. Recovery: `docker start searxng-new`. `always` (Firecrawl) DOES revive manual stops.

## `number_of_results: 0` is a red herring

A bare `search?q=x&format=json` from curl often returns `0` / no engines because
per-engine rate limits (Google/Brave anti-bot) report empty on cold requests. Health
is judged by the HTTP 200 + the bridge returning ranked results — NOT the raw count
on a curl one-off. Don't "fix" copy that isn't broken.

## User expectations ("bring it up properly and make it stay up")

When the user asks to make a service stay up, they mean BOTH:
- durable restart policy (`unless-stopped` / `always`) — survives reboots and daemon restarts, AND
- the whole consumer chain (bridge → Hermes → Firecrawl) still works — not just the container.

Respect scope: recreate/diagnose the failing piece, but do NOT touch the bridge binary,
Hermes config, or Firecrawl unless the user says so. Report explicitly what changed
vs. what was left alone. Users get nervous the moment you recreate infra; a clear
"only SearXNG changed; bridge/config/Firecrawl untouched" table de-escalates fast.
Future agents: state the change/untouched split up front.