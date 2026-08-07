---
name: local-ai-backends
description: Free local LLM/embedding backends for AI tools and gateways.
---

# Local AI Backends (LLM + embeddings)

Handle the recurring task: some locally-installed AI tool needs an inference backend, and the user wants it local-first / zero-API-key. Covers probing a gateway's real capabilities, and the free embedding provisioning menu.

## Core rule: PROBE the gateway before recommending

Never trust a gateway's marketing copy about what it can serve. **Verify capability against the running instance** before telling the user a provider/model will work:

1. Find the real base URL. Gateways rarely run on the port their README claims. `ss -ltnp` to find the listening port, then hit `<base>/v1`.
2. Dump the catalog: `curl -s <base>/v1/models`. Inspect entries for an `embedding`/`dimensions` capability — many routers list LLM chat models but expose **zero embedding models**.
3. Test the endpoint directly with a concrete model, not just a GET:
   - `POST <base>/v1/embeddings` with a known good id (e.g. `text-embedding-3-small`).
   - Interpret errors: `provider/model` format error ⇒ requires prefixed model id; `No credentials for embedding provider: <X>` ⇒ that route needs a paid/API key; `model_not_found` ⇒ correct shape but id unknown.

Key pitfall: **a "free AI gateway" is typically LLM-ONLY.** OpenRouter, and free-tier gateways like the user's OmniRoute, almost always route free chat completions but have no free embeddings — the embedding endpoint exists but refuses with "No credentials for embedding provider" unless a paid key is present. Verify, don't assume.

## Free embedding menu (zero API keys first)

Priority order for this user (has an RTX GPU):

1. **Local Ollama `nomic-embed-text`** — the default local embedding for many tools (deeptutor hard-codes a nomic-embed fallback). `pacman -S ollama` (in official `extra` on Manjaro/Arch, no AUR), then `ollama pull nomic-embed-text`. Point the tool's embedding profile at the **Ollama native endpoint `http://localhost:11434/api/embed`**, model `nomic-embed-text`. Fully offline, no key, no quota. **Recommended.** (Pitfall: an `ollama` binding is hardwired to Ollama's native `/api/embed` — do NOT give it a generic `/v1/embeddings` server; see the binding map below.)
2. **Free cloud embeddings (need a free key signup, no local GPU):** Google Gemini (`gemini-embedding-001`, AI Studio), Jina (`jina-embeddings-v2-base-en`, jina.ai dev tier), Qwen / SiliconFlow (`text-embedding-v3`, `bge-m3`), Cohere (`embed-v3`, free tier).
3. **Skip it entirely** if the tool only uses embeddings for a RAG / Knowledge Base feature and the user only wants chat.

## Workflow for the common case (tool lacks embeddings)
- If user already points the tool's LLM at a local gateway, that does NOT give it embeddings — embeddings and chat are separate backends.
- Before standing up anything heavy, grep the tool's own code for its expected default embedding model/provider type (e.g. `grep -rE "nomic-embed|bge|embed" <packagedir>/src`) so you configure what it actually expects.**

## deeptutor-specific wiring (binding map, profile schema, on-demand)

**Binding → adapter map** decides WHICH server a given binding accepts (`deeptutor/services/config/provider_runtime.py`, `services/embedding/adapters/`):
- `ollama` → **Ollama native** `POST /api/embed` (payload `{"model","input","keep_alive"}`, parses `data["embeddings"]`). NOT OpenAI-compatible.
- `vllm` (UI label "vLLM / LM Studio", alias `lmstudio`) → `openai_compat` → generic **`POST /v1/embeddings`**. Use THIS for llama.cpp server / LM Studio / vLLM.
- Others: `openai`, `custom`, `azure_openai`, `cohere`, `jina`, `siliconflow`, `aliyun`, `openrouter`, `custom_openai_sdk`.
- **base_url auto-detect quirk:** resolver keys off base_url when binding hint is absent — url contains `11434` ⇒ forced `ollama`, other localhost ⇒ forced `vllm`. Keep binding and base_url consistent.

**Profile store** = `data/user/settings/model_catalog.json` → `services.embedding.profiles[]` with `{id, name, binding, base_url, api_key, api_version, extra_headers, models:[{id,name,model,dimension,supported_dimensions}]}`, plus service-level `active_profile_id`/`active_model_id`. `provider_mode` is `local` (no key) when base_url is localhost.

**On-demand (don't hog memory/VRAM) — three escalating layers:**
0. **Not resident at all (strongest, when user says "runs on demand only"):** stop AND disable the service so the daemon isn't even sitting with models/port bound when idle. `sudo systemctl disable --now ollama`. Verify it's actually gone: `systemctl is-active ollama` → `inactive`, `systemctl is-enabled ollama` → `disabled`, and `ss -tlnp | grep 11434` → **no listener** (the port closing is the real proof the daemon is down). Then start it only when a client calls it: `sudo systemctl start ollama`.
1. Server unload policy: systemd drop-in `/etc/systemd/system/ollama.service.d/10-keepalive.conf` → `Environment=OLLAMA_KEEP_ALIVE=0`. Verify `journalctl -u ollama` shows `OLLAMA_KEEP_ALIVE:0s` and `curl -s http://127.0.0.1:11434/api/ps` → `{"models":[]}`.
2. **Tool/client side:** deeptutor's Ollama adapter hardcodes `keep_alive: "5m"` in the request, which pins the model regardless of the server setting — patch it to `"0"`. Always check the tool's adapter for a hardcoded keep_alive before trusting server-level config.

Verify through the tool's own code, not just curl: inside the pipx venv, call `resolve_embedding_runtime_config()` then `get_embedding_client().embed_sync([...])` (returns raw `List[List[float]]`; the client's async `embed` returns the same — no `.embeddings` attr).

Ollama on Blackwell (RTX 5060 Ti / sm_120) at 0.32.6 runs **CPU-only** (no sm_120 CUDA/Vulkan). Fine for embeddings — keeps the GPU completely free.

## Workflow for the common case (tool lacks embeddings)
- Offer the Ollama-local path first (fits the "free + uses my GPU" profile); only fall back to a free cloud key if the user declines local install.

See `references/omniroute-deeptutor-embeddings.md` for the concrete discovery + telemetry from one real session (OmniRoute catalog probing, deeptutor's embedding profile types), and `references/deeptutor-ollama-setup.md` for the full Ollama-on-demand setup: adapter map, model_catalog.json schema, keep_alive chain, and in-venv verification script.