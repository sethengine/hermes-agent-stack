---
source_session: "20260604_185710_e4868a"
date: 2026-06-13
category: software
tags: [hermes, npm, audit, monorepo, workspace, security, esbuild, vite]
related: [hermes-desktop-app, npm-workspaces-monorepo]
---

# Hermes NPM Audit Fix in Monorepo

## Root Cause of Failed Fix

Running `npm audit fix` from `apps/desktop/` fails because the Hermes desktop app is part of an **npm workspaces monorepo**. The lockfile lives in the **repo root** (`~/.hermes/hermes-agent/`), not inside subdirectories. All npm commands must run from the repo root.

## Vulnerabilities Fixed

| Vulnerability | Status |
|---|---|
| **joi 18.1.2** (moderate) | ✅ Fixed — `wait-on` → `joi@18.2.1` |
| **esbuild ≤0.28.0** (high, via vite) | ⚠️ 2 remaining — `--force` would break the build |

## Esbuild Warning — Don't Force

The 2 remaining esbuild warnings come through vite's transitive dependency chain. `npm audit fix --force` upgrades esbuild beyond what vite's `peerDependencies` allow, which breaks the desktop app build.

**Actual risk is low:**
- RCE vector requires a malicious npm registry
- File-read vulnerability is Windows-only (Linux is not affected)

**Recommendation:** Do not run `--force` unless you verify the desktop app still builds afterward.
