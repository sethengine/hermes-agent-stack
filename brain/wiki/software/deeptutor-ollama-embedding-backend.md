---
title: deeptutor Ollama Embedding Backend Setup
date: 2026-08-06
source_session: 20260806_185739_08083d
category: software
tags: [deeptutor, ollama, embeddings, local-ai, pipx, nomic-embed-text]
---

# deeptutor Ollama Embedding Backend

deeptutor is installed via `pipx` (v1.5.9). It requires an embedding model; the first install failed because `python-json-repair` (a dependency) is **not** in AUR — install it separately with `pipx install python-json-repair`.

## Free, on-demand embedding backend (no API key)

OmniRoute and OpenRouter have no free embedding models, so the working solution is a local **Ollama** backend:

- **Ollama 0.32.6** installed from Manjaro `extra` (binary at `/usr/bin/ollama`).
- **Model:** `nomic-embed-text` (768-dim, ~274 MB).
- **On-demand unload:** `keep_alive=0` → model frees after each request; `/api/ps` shows no model loaded at idle.
- **Runs CPU-only** — the RTX 5060 Ti (sm_120) is not detected by Ollama for GPU, which is fine for embeddings.

## LLM (chat) provider — OmniRoute

deeptutor's interactive setup tour configures the chat provider separately from the embedding profile baked into `model_catalog.json`:
- **Binding:** `openai`
- **Base URL:** `http://localhost:20128/v1`
- **No API key required** — OmniRoute answers `/v1/chat/completions` without a key (routes free models like `qwen3.8-max-preview`).

## Related
- [[local-ai-backends]]
- [[omniroute-gateway]]
- [[ollama-nomic-embedding]]