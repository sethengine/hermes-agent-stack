---
source_session: 20260611_190438_422897
date: 2026-06-11
category: software
tags: [brain, wiki, categories, structure, conventions]
---

# Brain Wiki Category Structure

The brain wiki organizes knowledge into category directories under `~/.hermes/brain/wiki/`.

## Directory Conventions

```
~/.hermes/brain/wiki/
  ├── software/       # Tooling, configs, skills, workflows
  ├── system/         # OS-level configs, systemd, kernel params
  ├── audio/          # PipeWire, ALSA, audio fixes
  ├── gpu/            # NVIDIA, AMD, driver issues, XID errors
  ├── kernel/         # Kernel params, modules, patches
  ├── ml/             # ML/AI tooling, training, inference
  └── research/       # Research skills, papers, agent setups
```

## File Naming

- Lowercase with hyphens: `pipewire-coil-whine-fix.md`
- Descriptive but concise: `nvidia-xid-31-workaround.md`
- Each file includes YAML frontmatter with `source_session`, `date`, `category`, and `tags`

## Linking Convention

Use `[[wiki-links]]` to cross-reference related concepts within the brain. The graphify extractor picks these up as explicit relationships.

## Categories Determined By

When the LLM extracts knowledge from a session, it assigns the best category based on the topic. If multiple categories apply, the primary category is chosen and cross-links are added via [[wiki-links]].

See also: [[global-session-brain-architecture]], [[brain-knowledge-extraction-pipeline]], [[brain-commands-reference]]
