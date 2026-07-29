---
name: llm-inference
description: "Run and serve large language models locally: llama.cpp GGUF inference, vLLM serving, Outlines structured generation, and model surgery."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Inference, LLM, GGUF, Quantization, vLLM, Outlines, Structured-Generation, Serving]
---

# LLM Inference

Local and high-throughput inference for large language models.

---

## llama.cpp (GGUF)

Local inference on CPU, Apple Silicon, CUDA, ROCm, and Intel GPUs.

### Model Discovery
Prefer URL workflows before custom scripts:
```bash
# Find GGUF files for a repo
python3 -m llama_cpp.hf_hub --model "TheBloke/Llama-2-7B-GGUF" --file "*.gguf"
```

### Server
```bash
python3 -m llama_cpp.server --model "model.gguf" --n_gpu_layers 35
```

### Quantization selection (model-agnostic comparison)

Compare formats generically by **bits per weight** — the fundamental property driving VRAM, speed, and quality:

| Format | Bits | Type | Quality vs FP16 | Speed vs FP16 | Hardware |
|---|---|---|---|---|---|
| Q8_0 | 8.5 | Int block | ~99.95% | ~1.5× | Any |
| **Q6_K** | **~6.6** | **Int k-quant** | **~99.5%** | **~1.8-2.2×** | **Any (CPU/GPU)** |
| FP8 | 8 | Float | ~99.9% | ~2× | Ada/Hopper+ |
| Q4_K_M | ~4.8 | Int k-quant | ~98.5% | ~2.5-3× | Any |
| **NVFP4** | **~4.0** | **Float (E2M1)** | **~95-99%** (size-dep.) | **~3.5-3.8×** | **Blackwell only** |
| MXFP4 | ~4.25 | Float (E2M1) | ~90-97% | ~3.5× | Blackwell (planned) |
| AWQ INT4 | ~4.0 | Int | ~99% | ~2-3× | Ada/Hopper+ (vLLM) |

**Key insights:**
- **Q6_K is the universal quality sweet spot** — works on any GPU or CPU, 99.5% of BF16, no ecosystem lock-in
- **NVFP4 wins on VRAM efficiency** (4× smaller than FP16) and Blackwell throughput, but has a hard-reasoning quality cliff (~80% recovery on MMLU-Pro) on small-to-mid models. Recovers to ~99% at 70B+ scale.
- **AWQ INT4 is the best 4-bit format overall** — beats NVFP4 on both quality AND throughput on Blackwell (proven on 397B MoE).
- **MXFP4 trails NVFP4 by ~10% accuracy** due to coarser block size (32 vs 16) and power-of-two scaling.
- **Perplexity does not predict real-world task quality** — always validate on downstream benchmarks.

**For detailed comparison** (VRAM formulas, absolute tok/s benchmarks, accuracy by model size, ecosystem lock-in, decision matrix): see `references/quantization-format-comparison.md`.

**General defaults:**
- Q4_K_M for most local use (best quality/size/tradeoff, universal)
- Q6_K or Q8_0 for maximum fidelity
- NVFP4 when on Blackwell and need max speed or extreme VRAM efficiency
- IQ quants for extreme compression on CPU

**Full docs:** See `references/llama-cpp/SKILL.md` and `references/llama-cpp/`.

---

## Outlines

Structured text generation with zero-overhead grammar control. Guarantees valid JSON/XML/code via Pydantic or JSON Schema.

### Quick Start
```bash
pip install outlines
```

### Example
```python
from pydantic import BaseModel
import outlines

class Character(BaseModel):
    name: str
    age: int

model = outlines.models.transformers("microsoft/DialoGPT-medium")
generator = outlines.generate.json(model, Character)
character = generator("Give me a character description")
```

**Full docs:** See `references/outlines/SKILL.md` and `references/outlines/`.

---

## Model Surgery (Obliteratus)

Abliterate LLM refusals and unwanted behaviors via diff-in-means and other surgical interventions.

### When to use
- Remove refusals from local models
- Tune model behavior without full retraining
- Research interpretability and steering

**Full docs:** See `references/obliteratus/SKILL.md` and `references/obliteratus/`.

---

## Comparison

| Tool | Best For | Backend |
|---|---|---|
| llama.cpp | Local CPU/GPU inference, edge deployment | GGUF |
| vLLM | High-throughput serving, batched requests | CUDA/ROCm |
| Outlines | Structured output, type-safe generation | Any (Transformers, vLLM, llama.cpp) |
| Obliteratus | Refusal removal, behavior surgery | Pytorch |
