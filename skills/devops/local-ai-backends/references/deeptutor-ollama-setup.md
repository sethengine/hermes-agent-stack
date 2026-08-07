# deeptutor + Ollama embeddings — adapter map, catalog schema, on-demand (2026-08)

Session follow-up to `omniroute-deeptutor-embeddings.md`: after confirming OmniRoute has no
free embeddings, the user chose **local Ollama, on-demand** (no resident model, no VRAM/memory hog).

## deeptutor embedding binding → adapter map (the key to "which server works")

Read from `deeptutor/services/config/provider_runtime.py` + `services/embedding/adapters/`:

| Binding (UI / profile `binding`) | Adapter | Endpoint shape |
|---|---|---|
| `ollama` | `ollama.py` | **Native Ollama** `POST /api/embed` (payload `{"model","input","keep_alive"}`; parses `data["embeddings"]`). NOT OpenAI-compatible. |
| `vllm` (UI label "vLLM / LM Studio", alias `lmstudio`) | `openai_compat` | **Generic OpenAI** `POST /v1/embeddings` (standard `{"data":[{"embedding":[...]}]}` shape). This is the one to use for llama.cpp server, LM Studio, vLLM. |
| `openai`, `custom`, `azure_openai`, `cohere`, `jina`, `siliconflow`, `aliyun`, `openrouter`, `custom_openai_sdk` | provider adapters | as named |

Implications:
- **llama.cpp server DOES work with deeptutor** — through the `vllm` binding, NOT `ollama`.
  `llama-server --embedding` exposes `/v1/embeddings` (OpenAI shape), which `openai_compat` parses.
- The `ollama` binding cannot point at a generic `/v1/embeddings` server (llama.cpp etc.) — it
  speaks Ollama's native protocol only.

### base_url auto-detection quirk (provider_runtime.py ~line 783)
The resolver keys off `base_url` when the binding hint is absent/unknown:
- url contains `11434` → forces `ollama`
- other localhost → forces `vllm`
So binding and base_url must agree; writing `binding: "ollama"` with a non-11434 localhost URL
gets overridden to `vllm`.

## model_catalog.json schema (deeptutor profile store)

Location: `data/user/settings/model_catalog.json` (under the deeptutor data dir).
`services.embedding`:

```json
{
  "services": {
    "embedding": {
      "active_profile_id": "ollama-local-embed",
      "active_model_id": "ollama-nomic-embed-text",
      "profiles": [
        {
          "id": "ollama-local-embed",
          "name": "Ollama (local, on-demand)",
          "binding": "ollama",
          "base_url": "http://127.0.0.1:11434/api/embed",
          "api_key": "",
          "api_version": "",
          "extra_headers": {},
          "models": [
            {
              "id": "ollama-nomic-embed-text",
              "name": "nomic-embed-text",
              "model": "nomic-embed-text",
              "dimension": "768",
              "supported_dimensions": ""
            }
          ]
        }
      ]
    }
  }
}
```

Notes:
- `dimension` may be left `""` → test_runner auto-fills from the API response on first test.
- `supported_dimensions` = CSV of dims from the last successful test (drives UI dropdown).
- Service-level `active_profile_id` + `active_model_id` MUST point at the entries, else the
  loader auto-picks `profiles[0]` / `models[0]` and rewrites the file.
- `provider_mode` comes out as `local` when base_url is localhost — no api_key needed.

## On-demand Ollama (no memory/VRAM hog) — the full chain

User requirement: model must not stay resident. Three layers, ALL needed:

1. **Server-level keep_alive** — systemd drop-in
   `/etc/systemd/system/ollama.service.d/10-keepalive.conf`:
   ```
   [Service]
   Environment=OLLAMA_KEEP_ALIVE=0
   ```
   Verify in `journalctl -u ollama`: `OLLAMA_KEEP_ALIVE:0s`. Confirm idle unload:
   `curl -s http://127.0.0.1:11434/api/ps` → `{"models":[]}`.
2. **Client/tool-side keep_alive** — deeptutor's Ollama adapter hardcodes
   `keep_alive: "5m"` in the request payload, which DEFEATS the server setting (a request with
   keep_alive>0 pins the model). Patch `services/embedding/adapters/ollama.py`
   `"keep_alive": "5m"` → `"keep_alive": "0"` (pipx venv file, user-writable). Check the tool's
   adapter for any hardcoded keep_alive before trusting server-level config.
3. **Start-on-demand** — `systemctl enable --now ollama` is fine; `keep_alive=0` means the
   server runs but holds no model between requests. No model = ~0 extra VRAM.

## Verify through the tool's own code (not just curl)

Best-practice check that the profile actually resolves + embeds:
```bash
VENV=/home/sethengine/.local/share/pipx/venvs/deeptutor
"$VENV/bin/python" - <<'PY'
import sys
sys.path.insert(0, "$VENV/lib/python3.14/site-packages")
from deeptutor.services.config import resolve_embedding_runtime_config
from deeptutor.services.embedding import get_embedding_client

cfg = resolve_embedding_runtime_config()
print(cfg.model, cfg.binding, cfg.effective_url, cfg.provider_mode)
# expect: nomic-embed-text ollama http://127.0.0.1:11434/api/embed local

client = get_embedding_client()
vecs = client.embed_sync(["hello world", "deeptutor test"])  # returns List[List[float]]
print(len(vecs), len(vecs[0]))  # expect: 2 768
PY
```
Pitfalls hit: client method is `embed_sync(texts)` / async `embed(...)` returning the raw list
(no `.embeddings` attr); `EmbeddingClient` lives in `deeptutor.services.embedding`.

## Ollama on Blackwell (RTX 5060 Ti, sm_120) — note

Ollama 0.32.6 on this machine ran **CPU-only** (`inference compute ... library=cpu`,
`total_vram="0 B"`; CUDA/Vulkan did not pick up sm_120). For a 274 MB embedding model this is
fine — arguably better, since it keeps the GPU entirely free. If later serving a chat model via
Ollama and GPU acceleration matters, that's a separate tuning step; embedding workloads can stay
on CPU.
