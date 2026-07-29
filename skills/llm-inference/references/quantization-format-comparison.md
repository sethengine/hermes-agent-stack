# Quantization Format Comparison: Q6_K vs FP8 vs NVFP4 vs MXFP4

Research compiled June 2026. Sources include arXiv papers, Red Hat/NVIDIA/OCP publications, community KLD evaluations, and HuggingFace benchmarks.

---

## The Fundamental Property: Bits Per Weight

This drives everything else — VRAM, speed, and quality are all downstream of this number:

| Format | Bits/weight | Compression vs FP16 | Type | Scale mechanism |
|---|---|---|---|---|
| FP16 (baseline) | 16 | 1× | Float | — |
| Q8_0 | 8.5 | 1.9× | Integer block | FP16 per 32-weight block |
| **Q6_K** | **~6.6** | **~2.4×** | **Integer k-quant** | **Per-layer variable, per-256-weight superblock** |
| FP8 (E4M3) | 8 | 2× | Float | Per-tensor (Hopper/Ada native TC) |
| Q5_K_M | ~5.7 | ~2.8× | Integer k-quant | Mixed-per-layer |
| Q4_K_M | ~4.8 | ~3.3× | Integer k-quant | Mixed-per-layer |
| **NVFP4** | **~4.0** | **4×** | **Float (E2M1)** | **FP8 E4M3 scale per 16-weight block + FP32 tensor scale** |
| MXFP4 | ~4.25 | ~3.8× | Float (E2M1) | E8M0 power-of-two scale per 32-weight block |
| INT4 AWQ | ~4.0 | 4× | Integer | Per-channel + salient weight protection |

---

## VRAM (model-agnostic formulas)

```
weights = params × bits_per_weight / 8
KV_cache = 2 × n_layers × d_model × seq_len × kv_bytes
Total = weights + KV_cache + ~1-2 GB overhead
```

### Weight-only sizes

| Format | 7B model | 12B model | 27B model | 70B model |
|---|---|---|---|---|
| FP16 | ~14 GB | ~24 GB | ~54 GB | ~140 GB |
| FP8 | ~7 GB | ~12 GB | ~27 GB | ~70 GB |
| Q8_0 | ~7.5 GB | ~13 GB | ~29 GB | ~74 GB |
| **Q6_K** | **~5.8 GB** | **~9.8 GB** | **~22 GB** | **~58 GB** |
| Q5_K_M | ~5.0 GB | ~8.5 GB | ~19 GB | ~50 GB |
| Q4_K_M | ~4.2 GB | ~7.0 GB | ~16 GB | ~42 GB |
| **NVFP4** | **~3.5 GB** | **~6 GB** | **~14 GB** | **~35 GB** |
| INT4 AWQ | ~3.5 GB | ~6 GB | ~14 GB | ~35 GB |

### KV cache impact (for a ~12B model, 48 layers, d_model ~4096)

| Context | KV @ FP16 | KV @ FP8/int8 |
|---|---|---|
| 8K | ~0.5 GB | ~0.25 GB |
| 32K | ~2 GB | ~1 GB |
| 128K | ~8 GB | ~4 GB |
| 256K | ~16 GB | ~8 GB |

### Total for Gemma 4 12B at 256K context

| Format | Weights | KV (fp8) | Total | Status on 16GB GPU |
|---|---|---|---|---|
| **Q6_K** | 9.8 GB | 8 GB | **~18 GB** | ❌ Needs 24GB |
| **NVFP4** | 6 GB | 8 GB | **~14 GB** | ✅ Fits with headroom |
| Q4_K_M | 7.2 GB | 8 GB | **~15.2 GB** | ✅ Tight |
| Q5_K_M | 8.5 GB | 8 GB | **~16.5 GB** | ❌ Barely fits |
| Q8_0 | 13 GB | 8 GB | **~21 GB** | ❌ Needs 24GB |

---

## Tokens per Second (decode, bandwidth-limited)

```
tok/s ≈ memory_bandwidth × utilization_eff / (weights_bytes + kv_bytes_per_token)
```

### Relative decode speed (12B model)

| Format | GB/step (weights) | Relative speed | Notes |
|---|---|---|---|
| FP16 | 24 GB | 1× (baseline) | — |
| FP8 | 12 GB | ~2× | Zero dequant overhead, native TC |
| **Q6_K** | **~10 GB** | **~1.8-2.2×** | 10-20% dequant math overhead |
| **NVFP4** | **~6 GB** | **~3.5-3.8×** | Near-native on Blackwell, some overhead |
| Q4_K_M | ~7 GB | ~2.5-3× | Most efficient GGUF quant |

### Prefill (prompt processing)

| Format | Prefill characteristic |
|---|---|
| Q6_K | ~500-1200 tok/s (bandwidth-bound + dequant) |
| FP8 | ~2000+ on Hopper (native 2× FP16 TC matmul) |
| NVFP4 | ~4000+ on Blackwell (native 4× FP16 TC matmul) |

### Real-world examples

| Setup | Format | tok/s | Source |
|---|---|---|---|
| Qwen3.5-397B-A17B (8× RTX PRO 6000) | AWQ INT4 | 152 (C=1) | KLD eval repo |
| Qwen3.5-397B-A17B (8× RTX PRO 6000) | NVFP4 | 132 (C=1) | KLD eval repo |
| Gemma 4 26B A4B (RTX PRO 6000) | NVFP4 | ~130 (C=1) | lna-lab |
| Gemma 4 12B (RTX 5070 Ti) | Q6_K | ~60 | NVIDIA Forums |
| Qwen3.6-27B (RTX 5090) | NVFP4+MXFP6 | ~74-77 | HF michaelw9999 |
| Llama 3.1 8B (RTX 4090) | Q6_K | ~110-130 | Community |

---

## Accuracy (vs BF16 baseline)

### General hierarchy

```
Q8_0 (~99.95%) > FP8 (~99.9%) > Q6_K (~99.5%) > Q5_K_M (~99.0%)
> NVFP4 (large models ~99%, small models ~95-98%)
> Q4_K_M (~98.5%) > MXFP4 (~90-97%) > Q3_K_M (~95%)
```

### Key research findings

**arXiv 2510.25602 (INT vs FP, HKU/ByteDance):**
- At 8-bit: INT beats FP (MXINT8 > MXFP8)
- At 4-bit: FP beats INT, but NVINT4 with Hadamard rotation surpasses NVFP4
- Crossover point depends on crest factor (outlier magnitude in tensors)

**Red Hat NVFP4 accuracy by model scale (Feb 2026):**
- **70B-235B:** ~99% recovery of BF16 — near-lossless
- **~30B:** 97-99% recovery
- **7B-14B:** 95-98% recovery — notable variance, worse on hard reasoning
- **MoE:** Exceptionally robust (NVFP4's FP8 scales handle sparse expert activations well)

**ai.rs benchmarks (Qwen3-8B, RTX 5090):**
- MMLU (general): 97.5% recovery ✅
- GSM8K (math): 99.4% recovery ✅
- MMLU-Pro (hard reasoning): **79.4% recovery ⚠️** — NVFP4's biggest weakness
- AIME24 (math olympiad): **81.8% recovery ⚠️**
- Q6_K at the same size: 98%+ across ALL tasks

**KLD evaluation (397B MoE, vs FP8 reference):**
- AWQ INT4: Mean KLD 0.024 (near-lossless tier)
- NVFP4: Mean KLD 0.035 (good, minimal loss)
- Q6_K at comparable size (not directly tested on 397B): expected ~0.02-0.04 range

**michaelw9999 Qwen3.6-27B (direct Q6_K vs NVFP4):**
| Benchmark | Q6_K | NVFP4 | NVFP4+MXFP6 mixed |
|---|---|---|---|
| Average | 87.9% | 88.2-90.4% | 94.0% |
| Perplexity ratio | — | 1.105-1.13 | 1.027 |

### The hard-reasoning problem with NVFP4

NVFP4 consistently shows a **sharp quality cliff on hard reasoning tasks** (MMLU-Pro, AIME) that doesn't appear on general knowledge (MMLU, GSM8K). This is an architectural limitation of having only 8 unique FP4 values per block — complex multi-step reasoning apparently requires finer weight resolution.

Q6_K with its ~200+ effective quantization levels doesn't show this cliff.

---

## Ecosystem Lock-in

This is the deciding factor for most users — you don't choose just the format, you choose the runtime:

| | Q6_K (GGUF) | FP8 (vLLM/TRT-LLM) | NVFP4 (vLLM) | MXFP4 (vLLM/OCP) |
|---|---|---|---|---|
| **Engine** | llama.cpp, Ollama, LM Studio | vLLM, TRT-LLM, TGI | vLLM (nightly), TRT-LLM | vLLM (experimental) |
| **GPU req** | Any (CPU fallback) | Ada/Hopper+ (SM 8.9+) | Blackwell only (SM 10/12) | Blackwell planned |
| **Setup** | `ollama pull` — trivial | Docker + config | Nightly builds + CUDA 13 — painful | Rare checkpoints |
| **Model availability** | Thousands of GGUF on HF | Hundreds FP8 | ~10-20 models total | Very few |
| **Multi-GPU** | Via llama.cpp | Native vLLM | Native vLLM | Native vLLM |
| **LoRA** | Yes | Yes (vLLM) | Not yet (No LoRA) | Not yet |
| **Windows** | Native .exe | WSL2/Linux | WSL2 (nightmare) | Linux only |
| **CPU fallback** | Yes | No | No | No |

---

## Critical Pitfalls

### 1. Perplexity does NOT predict real-world task quality

Unsloth found that MXFP4 often looks better on perplexity (PPL) but worse on downstream benchmarks (LiveCodeBench, reasoning). Q3_K sometimes has better PPL than Q4_K. **Always use task-specific benchmarks, not PPL alone.**

### 2. NVFP4's hard reasoning cliff

On small-to-mid models (7-30B), NVFP4 drops to 79-82% recovery on MMLU-Pro and AIME — a 20% quality loss on the hardest tasks. This doesn't show in MMLU (general) or GSM8K. If your use case involves complex reasoning, prefer Q6_K.

### 3. MXFP4 is measurably worse than NVFP4

arXiv 2603.08713: MXFP4 has a ~10% accuracy gap vs NVFP4 due to: (a) coarser block size (32 vs 16), (b) E8M0 power-of-only scaling with no mantissa. OAS+MBS software fixes can close this to ~1%, but are not yet standard in any runtime.

### 4. GGUF per-layer quantization matters

Q6_K and Q4_K_M allocate different bit widths per layer — attention layers get more bits, MLP layers get fewer. NVFP4 and MXFP4 are uniform across all layers. This structural advantage partially compensates for Q6_K's lower bit count vs NVFP4 on sensitive layers.

### 5. NVFP4 checkpoints vary in quality

NVIDIA's NVFP4 keeps attention in higher precision; Red Hat's compresses attention too. This creates a size-quality tradeoff that is opaque without checking individual model cards. Always check which layers are quantized.

---

## Decision Matrix (model-agnostic)

| Condition | Best format | Why |
|---|---|---|
| **Any GPU, max quality** | Q6_K | 99.5% of BF16, works everywhere |
| **Any GPU, max speed** | Q4_K_M | Best engine/format maturity, ~3× speedup |
| **Blackwell, max speed** | NVFP4 | ~4× FP16 speed, 4× compression |
| **Blackwell, max quality** | Q6_K via Ollama or NVFP4 on large models | Q6_K for small, NVFP4 catches up at 70B+ |
| **VRAM constrained (<16GB)** | Q4_K_M or NVFP4 (on Blackwell) | Q4_K_M = 7 GB, NVFP4 = 6 GB for a 12B |
| **Long context (128K+)** | NVFP4 (+ fp8 KV) | Leaves room for huge KV cache |
| **70B+ model** | NVFP4 | 99% recovery at this scale, Q6_K won't fit |
| **Hard reasoning / math / code** | Q6_K | NVFP4 drops to 80% on MMLU-Pro |
| **Multi-user serving** | AWQ INT4 or FP8 (vLLM) | AWQ beats NVFP4 on both quality AND throughput |
| **Windows user** | Q6_K (GGUF) | Native .exe, no WSL2 needed |

---

## Quick Reference: Key Numbers

- Q6_K = 6.6 BPW, ~99.5% quality, works on literally anything
- NVFP4 = 4.0 BPW, ~95-99% quality (size-dependent), Blackwell-only
- MXFP4 = 4.25 BPW, ~90-97% quality, about 10% worse than NVFP4 without fixes
- FP8 = 8 BPW, ~99.9% quality, Ada/Hopper/Blackwell via vLLM
- INT4 AWQ = 4.0 BPW, ~99% quality (best 4-bit overall), Ada/Hopper/Blackwell via vLLM
- Q4_K_M = 4.8 BPW, ~98.5% quality, universal via GGUF
