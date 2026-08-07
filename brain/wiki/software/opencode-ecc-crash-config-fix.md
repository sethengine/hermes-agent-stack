---
source: "20260726_014135_b785a2"
date: "2026-07-26"
category: "software"
tags: [opencode, ecc, crash, config, sigabrt, nodeservice, tools, symlink]
---

# OpenCode Crash After ECC Install — Config Path Fix + Tools Symlink Fix

## The Problem

Installing **ECC (Everything Claude Code / Enhanced Cursor Chat, github.com/affaan-m/ECC)** to `~/.opencode/` breaks OpenCode's desktop app in **two ways**:

1. **Plugin/skills config paths** — ECC generates `opencode.json` with incorrect paths
2. **Tools directory** — OpenCode auto-discovers the `tools/` directory and attempts to load **TypeScript source** files instead of compiled JavaScript

Result: NodeService utility subprocess crashes with **SIGABRT (Signal 6, SI_TKILL)** ~2 min after startup — OpenCode stops responding to prompts.

## Fix 1: Config Paths

Two config values in `opencode.json` need correcting:

| Field | ECC's (broken) value | Correct value |
|-------|---------------------|---------------|
| `plugin` | `./plugins` | `./dist/plugins` |
| `skills.paths` | `../skills` | `./skills` |

**Two configs require patching:**
1. `~/.opencode/opencode.json` — Home/user-level config
2. `src/git/ECC/.opencode/opencode.json` — Project-level config

## Fix 2: Tools Directory Symlinks

Even with the config fix, the crash persists. OpenCode auto-discovers the `tools/` directory and tries to load TypeScript source files. Create symlinks to the compiled JS outputs:

```bash
cd /opt/OpenCode

# Tools: symlink each .js to compiled dist version
for f in tools/*.js; do
  ln -sf "../dist/$f" "$f"
done

# Plugins: symlink to compiled outputs
ln -sf dist/plugins/index.js plugins/index.js
ln -sf dist/plugins/ecc-hooks.js plugins/ecc-hooks.js
ln -sf dist/plugins/lib/chan* plugins/lib/
```

This ensures OpenCode loads compiled JavaScript, not raw TypeScript source. The crash kills the NodeService process which handles LLM prompts — hence "no response" from the app.

## Important

Reinstalling ECC (even with `full` profile) **overwrites** the config fix — both configs must be re-patched after reinstall. Missing instruction files from a `minimal` install are harmless warnings, not crash causes.

## Related

- [[software_opencode-nodeservice-crash]] — OpenCode NodeService crash (different root cause)
- [[software_hermes-opencode-skills-repos]] — OpenCode skills/config