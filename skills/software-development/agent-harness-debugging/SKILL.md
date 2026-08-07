---
name: agent-harness-debugging
description: "Debug crashes, config issues, and plugin loading failures in AI coding agent harnesses (OpenCode, Claude Code, Cursor, Codex). Covers Electron Node.js service crashes, config resolution paths, cross-harness integration debugging, and ECC (Everything Claude Code) integration patterns."
version: 1.0.0
author: sethengine
platforms: [linux]
metadata:
  hermes:
    tags: [debugging, agent-harness, opencode, ecc, electron, plugins, config]
    related_skills: [systematic-debugging, desktop-app-profiling, cross-platform-skill-porting]
---

# Agent Harness Debugging

## Overview

AI coding agent harnesses (OpenCode, Claude Code, Cursor, Codex) use plugin systems, tool registries, and config-driven initialization. When these go wrong, the Node.js/Electron utility process crashes silently — the app UI stays open but won't respond to prompts.

## Core Principle: Investigate First, Report, Then Fix

**NEVER modify agent harness config files during investigation.** Configs like `opencode.json`, `.cursor/settings.json`, `.claude/claude.json`, and ECC's `.opencode/` files are Phase 4 (fix) actions.

**Required workflow:**
1. Investigate (read-only: logs, configs, process info, journal)
2. Report findings to the user
3. Wait for approval or explicit "fix it" before patching anything

Configs in `~/.opencode/`, `~/.claude/`, `~/.cursor/`, and similar harness directories are production state — modifying them without approval is equivalent to editing a running system's config.

## Common Crash Patterns

### 0. Tools Directory Loads TypeScript Source Instead of Compiled JS

**Signature:** Config paths are correct but OpenCode still crashes after an ECC install. The app starts, NodeService initializes, but prompts get no response because the Node.js service dies during tool loading.

**Root cause:** OpenCode auto-discovers the `tools/` directory and attempts to load `.js` files from it. After ECC install, `tools/` contains **TypeScript source files** with `.js` extensions, not actual compiled JavaScript. Electron's Node.js utility process tries to `require()` these pseudo-JS files, hits missing imports and syntax mismatches, and aborts.

**Diagnosis:**
```bash
# Check if tools/ files are real JS or TS-in-disguise
head -3 /opt/OpenCode/tools/*.js | grep -E "import |export |from "
# Real JS uses require/module.exports; TS-in-JS uses import/export
```

**Fix — symlink to compiled outputs:**
```bash
cd /opt/OpenCode
for f in tools/*.js; do
  ln -sf "../dist/$f" "$f"
done
# Also symlink plugins to compiled JS
ln -sf dist/plugins/index.js plugins/index.js
ln -sf dist/plugins/ecc-hooks.js plugins/ecc-hooks.js
```

This is the **second** ECC crash vector — the first being broken config paths (section 2). Both must be fixed for OpenCode to survive startup.

### 1. Node.js Utility Process SIGABRT

**Signature:** OpenCode desktop starts but prompts do nothing. Systemd records a coredump:

```
Signal: 6 (ABRT) si_code: SI_TKILL
```

The process kills itself (SIGABRT via `SI_TKILL`) on an unhandled exception — NOT an external crash.

**Where to look:**
- `journalctl --user -u app-ai.opencode.desktop-*.scope`
- `~/.config/ai.opencode.desktop/logs/<session>/`
- `~/.config/ai.opencode.desktop/opencode.global.dat` (contains notification history with plugin loading errors)

### 2. Plugin/Tool Loading Failures

Agent harnesses load tools and plugins from config. When the config points to TypeScript source files instead of compiled JavaScript, loading fails silently during startup but crashes when the user sends a prompt.

There are TWO distinct ECC tool-loading failure vectors:
- **Config path issue (this section):** Config's `plugin` field points to TS source dir instead of compiled `dist/`
- **Tools directory issue (section 0 above):** OpenCode auto-discovers `tools/` independently of config and loads TS-in-JS files

Either one alone can crash the Node.js service. Fix both.

**Check config paths:**
```bash
# OpenCode
grep -A2 '"plugin"' ~/.opencode/opencode.json
grep -A2 '"paths"' ~/.opencode/opencode.json

# Also check project-level configs
find . -name "opencode.json" -maxdepth 3 -not -path "*/node_modules/*"
```

**Correct values vs common mistakes:**
| Field | Broken | Fixed |
|-------|--------|-------|
| `plugin` | `"./plugins"` (TS source) | `"./dist/plugins"` (compiled JS) |
| `skills.paths` | `"../skills"` (wrong parent) | `"./skills"` (local dir) |

### 3. ECC (Everything Claude Code) Integration

ECC generates configs for multiple harnesses from a single repo. Known issues:

- **`opencode.json` paths are wrong after install**: The installer points `plugin` to the TypeScript source directory regardless of profile. The compiled `.js` files exist in `dist/` but the config doesn't reference them.
- **`tools/` directory contains TS-in-JS files**: Even after fixing config paths, OpenCode auto-discovers `tools/` and loads `.js` files directly. ECC installs TypeScript source files with `.js` extensions containing `import/export` syntax that Node.js cannot load. Fix: symlink `tools/*.js` → `dist/tools/*.js`.
- **Reinstall overwrites fixes**: Running the ECC installer again regenerates `opencode.json` with the broken default paths and restores TypeScript files to `tools/`. Fixes must be re-applied after every install.
- **Profile affects which files are copied**: `minimal` skips `agents-core`, `rules-core`; `full` skips `framework-language` and `machine-learning`. Referenced instruction files may be missing.

**Check the install state:**
```bash
cat ~/.opencode/ecc-install-state.json  # Inspect profile, modules, operations
```

### 4. Missing Instruction Files

Reference files listed in `instructions` may not exist if the corresponding module was skipped during install. These produce non-fatal warnings — they don't crash the process.

## Investigation Toolkit

### Log Locations

| Application | Log Path |
|-------------|----------|
| OpenCode desktop | `~/.config/ai.opencode.desktop/logs/<session>/main.log` |
| OpenCode crash | `~/.config/ai.opencode.desktop/logs/<session>/crash.log` |
| OpenCode utility | `~/.config/ai.opencode.desktop/logs/<session>/utility.log` |
| OpenCode global store | `~/.config/ai.opencode.desktop/opencode.global.dat` |
| OpenCode settings | `~/.config/ai.opencode.desktop/opencode.settings` |
| Systemd coredump | `coredumpctl list \| grep opencode` |
| Systemd journal | `journalctl --user -u app-ai.opencode.desktop-*.scope` |

### Config Files

| Type | Path |
|------|------|
| OpenCode home config | `~/.opencode/opencode.json` |
| OpenCode project config | `<project>/.opencode/opencode.json` |
| ECC install state | `~/.opencode/ecc-install-state.json` |
| OpenCode workspace data | `~/.config/ai.opencode.desktop/opencode.global.dat` |

### Key Commands

```bash
# Find plugin/tool loading errors in notification history
strings ~/.config/ai.opencode.desktop/opencode.global.dat | grep -i "plugin\|Failed to load\|Cannot find module"

# Check opencode.json for broken paths
grep -A2 '"plugin"\|"paths"\|"skills"' ~/.opencode/opencode.json

# Find all opencode.json files (excluding node_modules)
find ~ -name "opencode.json" -maxdepth 5 -not -path "*/node_modules/*" 2>/dev/null
```

## Fixes

### OpenCode Plugin Path

```patch
- "plugin": ["./plugins"]
+ "plugin": ["./dist/plugins"]
```

### OpenCode Skills Path

```patch
- "skills": { "paths": ["../skills"] }
+ "skills": { "paths": ["./skills"] }
```

Apply to BOTH `~/.opencode/opencode.json` and any project-level `.opencode/opencode.json`.

## Pitfalls

### DON'T modify config files during investigation

Patience. Read logs, inspect configs with `grep`/`cat`, trace the error chain. Don't write or patch anything until you've confirmed root cause AND gotten user approval. The user will call you out on this.

### DON'T assume "sidecar exited { code: 0 }" is normal

In OpenCode, the Node.js utility service is logged as a "sidecar." Code 0 can be misleading — SIGABRT (signal 6) translates to exit code 134 (128+6), but OpenCode may report 0. Correlate with systemd journal and coredumpctl.

### DON'T forget project-level configs

OpenCode loads `~/.opencode/opencode.json` as global config, but also loads `.opencode/opencode.json` from the current project directory. Apply fixes to both.

### DON'T re-run ECC installer without re-applying fixes

The ECC installer always writes `opencode.json` with broken paths. If you reinstall, you must re-apply the config patches.

## References

- `references/opencode-ecc-plugin-crash.md` — Full session walkthrough of debugging an OpenCode SIGABRT crash caused by ECC plugin loading failures. Includes exact error messages, investigation steps, and fix application.
