---
source: "20260711_190829_979025"
category: software
date: 2026-07-11
tags: [llama-server, hermes, config, profile, connection]
---

# Connecting Hermes Desktop to Local llama-server

Hermes Desktop can use a local llama-server as its LLM backend via the OpenAI-compatible endpoint.

## Setup

Create a dedicated profile (`llama`) and configure:

```bash
hermes config set model.provider custom --profile llama
hermes config set model.base_url http://127.0.0.1:8084/v1 --profile llama
hermes config set model.context_length 32768 --profile llama
hermes config set delegation.provider custom --profile llama
hermes config set delegation.base_url http://127.0.0.1:8084/v1 --profile llama
```

## Common Pitfall: Port Mismatch

The server runs on a specific port (e.g., 8084) but the default config often uses 8080. Both `model.base_url` and `delegation.base_url` must match the actual server port. Check with:

```bash
curl http://localhost:8084/v1/models
```

## After Config Change

Do `/new` in Hermes (or restart Hermes Desktop) for config changes to take effect. There is no `/reset` command in Hermes Desktop.

## References
- [[geforce-rtx-5060-ti]]
