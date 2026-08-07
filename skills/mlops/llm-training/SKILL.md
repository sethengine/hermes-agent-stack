---
name: llm-training
description: "Fine-tune large language models efficiently: Axolotl (YAML-based), Unsloth (fast LoRA/QLoRA), and TRL workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Fine-Tuning, LLM, LoRA, QLoRA, Axolotl, Unsloth, TRL, Training, Optimization]
---

# LLM Training

Fine-tune large language models with YAML configs, fast optimizers, and memory-efficient techniques.

---

## Axolotl

YAML-driven fine-tuning supporting 100+ models, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, and multimodal training.

### Quick Start
```bash
pip install axolotl
axolotl train config.yaml
```

### Common Patterns
- Validate data transfer speeds with NCCL Tests before large training jobs.
- Use `references/axolotl/` for API docs, dataset formats, and index.

**Full docs:** See `references/axolotl/SKILL.md` and `references/axolotl/`.

---

## Unsloth

2–5× faster LoRA/QLoRA fine-tuning with less VRAM. Supports Llama, Mistral, Gemma, Qwen.

### Quick Start
```bash
pip install unsloth
```

### Features
- Automatic gradient checkpointing optimization
- Support for 4-bit and 16-bit LoRA
- Integrates with HuggingFace TRL and PEFT

**Full docs:** See `references/unsloth/SKILL.md` and `references/unsloth/`.

---

## When to Use What

| Tool | Best For | Key Feature |
|---|---|---|
| Axolotl | YAML-config driven training, multimodal, RLHF (DPO/GRPO) | 100+ pre-configured models |
| Unsloth | Speed & VRAM efficiency on popular architectures | 2–5× faster, less memory |
| TRL | Research flexibility, custom reward models | Modular RLHF library |

---

## Hardware Requirements

- **Minimum:** 8GB VRAM (QLoRA, lazy loading)
- **Recommended:** 16GB+ VRAM for full fine-tuning
- **Distributed:** DeepSpeed / FSDP for multi-GPU
