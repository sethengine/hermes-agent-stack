---
title: OmniRoute Boot Service via Docker
date: 2026-08-06
source_session: 20260806_183539_2c1380
category: software
tags: [omniroute, docker, systemd, gateway, llm-routing, boot-service]
---

# OmniRoute Boot Service (Docker, not systemd-wrapped AppImage)

OmniRoute (diegosouzapw/OmniRoute) is a local OpenAI-compatible LLM gateway at `localhost:20128`. The correct way to run it as a persistent boot service is a **Docker container** — NOT wrapping the AppImage in systemd.

## Why not systemd + AppImage

The AppImage is the **Electron GUI** build. Its server process is not a proper foreground daemon, so systemd sees it exit/crash, and the Electron renderer misbehaves without a display. The program's actual server runs itself when launched correctly.

## Correct boot method (Docker)

```bash
docker run -d --name omniroute --restart unless-stopped \
  --stop-timeout 40 -p 20128:20128 -v omniroute-data:/app/data omniroute
```

- `--restart unless-stopped` recovers the container after reboot.
- `docker.service` is `enabled` at boot, so the container comes up on startup.
- Port check: ensure `20128` is free before creating the image/container.

## Related
- [[deeptutor-ollama-embedding-backend]]
- [[searxng-docker-setup]]
- [[docker-self-hosted-services]]