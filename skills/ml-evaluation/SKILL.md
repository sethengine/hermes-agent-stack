---
name: ml-evaluation
description: "Evaluate and track machine learning experiments: lm-eval-harness benchmarks and Weights & Biases experiment tracking."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MLOps, Evaluation, Benchmarks, Experiment-Tracking, Weights-and-Biases, WandB]
---

# ML Evaluation

Benchmark language models and track experiments systematically.

---

## lm-eval-harness

Run standard benchmarks (MMLU, GSM8K, Hellaswag, etc.) against any HuggingFace model or local endpoint.

### Quick Start
```bash
pip install lm-eval
lm-eval --model hf --model_args pretrained=meta-llama/Llama-2-7b-hf --tasks mmlu,gsm8k --batch_size auto
```

### Common Tasks
- `mmlu` — Multi-task language understanding
- `gsm8k` — Grade school math
- `hellaswag` — Commonsense reasoning
- `arc_challenge` — Science questions
- `truthfulqa_mc` — Truthfulness

---

## Weights & Biases

Track experiments, visualize training, compare runs, and manage model registries.

### Quick Start
```bash
pip install wandb
wandb login
```

### Logging
```python
import wandb
wandb.init(project="my-llm")
wandb.log({"loss": 0.5, "accuracy": 0.92})
```

### Features
- Real-time metric dashboards
- Hyperparameter sweeps
- Artifact versioning (datasets, models)
- Team collaboration workspaces

**Full docs:** See `references/weights-and-biases/SKILL.md` and `references/weights-and-biases/`.

---

## Best Practices

- Run benchmarks before and after fine-tuning to measure delta.
- Log everything to W&B for reproducibility.
- Use `lm-eval-harness` for standardized comparisons.
- Store benchmark configs as W&B artifacts for versioning.
