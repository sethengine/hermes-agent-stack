---
title: Gemma 4 12B — Community Consensus
date: 2026-06-13
source_session: 20260613_174852_cc821a
category: ml
---

# Gemma 4 12B — Community Consensus (as of mid-June 2026)

Google DeepMind released Gemma 4 12B on June 3, 2026. It is viewed as the new local-multimodal sweet spot for 16 GB hardware.

## Key facts

- Dense ~12 B parameter model, Apache 2.0, text/image/audio input, text output.
- Encoder-free unified architecture: ~35 M embedder replaces separate vision/audio encoders.
- Context window up to 256 K tokens; local footprint ~26.7 GB BF16, ~13.4 GB SFP8, ~6.7 GB Q4_0.
- Reported benchmarks: ~77.2% MMLU Pro, ~78.8% GPQA Diamond.
- Real-world speeds: ~21 tok/s on RTX 4060 (Q4); ~35 tok/s on M4 Max 40c (4-bit); ~60 tok/s on RTX 5070 Ti (Q6, llama.cpp).
- QAT checkpoints released June 5, 2026 reduce VRAM further; QAT at Q4_0 can beat naive PTQ.

## Known pitfalls

- "Approaches 26B MoE" is still a vendor claim; community validation is limited as of 2026-06-13.
- Code-heavy benchmarks lag behind the 26B/31B variants.
- Day-one fine-tuning tooling was rough: older HuggingFace transformers/PEFT did not recognize `gemma4` architecture out of the box.
- Naive GGUF Q4_0 conversion of QAT checkpoints can produce worse accuracy than naive PTQ; prefer Unsloth dynamic GGUFs or proper conversion pipelines.
- KV cache is less efficient than Qwen 3.5; `--flash-attn` and `kv-cache-dtype fp8` help significantly.

## Related

- [[gemma-4-family-overview]]
- [[local-llm-deployment]]
- [[quantization]]
