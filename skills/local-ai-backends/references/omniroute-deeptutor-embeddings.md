# OmniRoute + deeptutor — real discovery transcript (2026-08)

## OmniRoute (user's local gateway)

- Repo: `diegosouzapw/OmniRoute` — local-first OpenAI-compatible gateway, one endpoint, 290+ providers (90+ free), auto-fallback, token compression.
- Default port: **20128** (`http://localhost:20128/v1`). Zero-config start: `npm install -g omniroute && omniroute`.
- Dashboard: `http://localhost:20128`; API: `http://localhost:20128/v1`.
- Model ids are `provider/model` format (e.g. `opencode/qwen3.5-plus`). `model=auto` works for chat but **not** embeddings — `/v1/embeddings` with `auto` returns `Invalid embedding model: auto. Use format: provider/model`.
- `GET /v1/models` returns ~370 entries. **Zero of them expose an embedding capability / `dimensions` flag** — the free catalog (owned_by: opencode, combo, auggie, theoldllm, duckduckgo-web, felo-web, veoaifree-web, qwen-web, chipotle, mimocode) is 100% LLM chat.
- `POST /v1/embeddings` with `text-embedding-3-small` / `gemini-embedding-001` → `No credentials for embedding provider: openai` / `gemini`. So embeddings exist as a route but every backend requires a paid key; **no free embedding is available through OmniRoute**.

Conclusion: OmniRoute's free tier is LLM-only — same limitation as OpenRouter. Cannot be used as a free embedding backend.

## deeptutor

- Installed via pipx (v1.5.9). The AUR PKGBUILD's dep `python-json-repair` does not exist on PyPI; the real package is **`json-repair`** (import name `json_repair`). Workaround: `pipx install json-repair` (installs fine), or install deeptutor via pipx directly.
- Embedding model is used only for **Knowledge Base / RAG** features — optional for plain chat tutoring.
- Local embedding default in code: `nomic-embed-text` (also `nomic-embed` matched). Settings → Models → Embedding profile:
  - Type: **Local** (Ollama)
  - Base URL: `http://localhost:11434`
  - Model: `nomic-embed-text`
- Supported embedding provider types in package (grep `deeptutor/runtime/providers`): Local/Ollama, OpenAI, Gemini, Jina, Qwen, Cohere, SiliconFlow, Together, Baidu, HuggingFace, Novita.

## Free embedding decision (this user)

- User has RTX 5060 Ti + Manjaro. `ollama` 0.32.1 is in official `extra` repo (no AUR needed): `sudo pacman -S ollama && ollama pull nomic-embed-text`.
- Recommended: local Ollama nomic-embed-text. Alternatives (free key signup): Gemini `gemini-embedding-001` (AI Studio), Jina `jina-embeddings-v2-base-en`, Qwen/SiliconFlow `text-embedding-v3`/`bge-m3`, Cohere `embed-v3`.

## Probe commands that worked

```bash
ss -ltnp | grep -iE "omniroute|20128"          # find port
curl -s http://localhost:20128/v1/models > /tmp/or_models.json
python3 -c "import json; d=json.load(open('/tmp/or_models.json'))['data']; print([m['id'] for m in d if m.get('capabilities',{}).get('embedding')])"  # → [] (none)
curl -s -X POST http://localhost:20128/v1/embeddings -H 'Content-Type: application/json' -d '{"model":"text-embedding-3-small","input":"hi"}'
```
