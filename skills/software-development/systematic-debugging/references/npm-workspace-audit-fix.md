# NPM Workspace Audit Fix Debugging

## When `npm audit fix` Fails in Monorepos

Common failure modes when running `npm audit fix` in npm workspaces monorepos.

### 1. ENOLOCK — "Command requires an existing lockfile"

```
npm error code ENOLOCK
npm error audit This command requires an existing lockfile.
npm error audit Try creating one first with: npm i --package-lock-only
```

**Root cause:** You ran `npm audit fix` from a workspace subdirectory (e.g., `apps/desktop/`). In npm workspaces, the lockfile lives at the repo **root**, not inside individual workspace directories.

**Fix:** Always run npm commands from the repo root:

```bash
cd ~/.hermes/hermes-agent/   # or whatever the root is
npm audit
npm audit fix
```

### 2. "Cannot read properties of null (reading 'isDescendantOf' or 'edgesOut')"

```
npm error Cannot read properties of null (reading 'isDescendantOf')
npm error Cannot read properties of null (reading 'edgesOut')
```

**Root cause:** npm 11.x has known bugs with combining `audit fix` and workspace trees, especially when workspace packages have invalid/higher version ranges for transitive deps (e.g., a workspace declares `"esbuild": "^0.25.0"` but the hoisted version is `0.27.7`).

**Workaround — fix manually instead of relying on `npm audit fix`:**

```bash
# 1. Identify which dependencies have vulnerabilities
npm audit
# → esbuild (high), joi (moderate), etc.

# 2. For transitive deps that can be upgraded safely:
npm install wait-on@latest --save-dev --workspace=<workspace-name>
# This pulls in the fixed joi version indirectly

# 3. For packages needing --force (breaking change):
npm install <pkg>@<version> --force
# This upgrades the root copy but may leave workspace copies unchanged

# 4. Verify remaining vulnerabilities:
npm audit
```

### 3. Manual Transitive Dep Upgrade Strategy

When `npm audit fix` crashes, use `npm ls <pkg>` to trace where the vulnerable package comes from:

```bash
# Find who depends on the vulnerable package
npm ls joi
# → hermes@0.15.1 -> ./apps/desktop
#   → wait-on@9.0.5
#     → joi@18.1.2

# Then update the direct dependency (not the transitive one)
npm install wait-on@9.0.10 --save-dev --workspace=apps/desktop
# → joi@18.2.1 (fixed)
```

### Pattern: Root vs Workspace npm Commands

| Command | Root (workspaces monorepo) | Subdirectory |
|---------|---------------------------|--------------|
| `npm audit` | ✅ Works — scans all workspaces | ❌ ENOLOCK |
| `npm audit fix` | ⚠️ May crash on workspace issues | ❌ ENOLOCK |
| `npm install <pkg>` | ✅ Adds to root `node_modules` | ✅ But lockfile still at root |
| `npm install <pkg> --workspace=<ws>` | ✅ Scoped to workspace | — |

### When `--force` Is Required

The `--force` flag skips peer dependency version checks. Use it only when:

- The vulnerability is in a transitive dep through a tool like `vite` that pins a range
- You've verified the app still builds and runs after the upgrade
- You accept the risk of peer dep mismatches

**Always verify after force upgrade:**

```bash
# Check if the app/desktop still builds
cd apps/desktop && npm run build
```

### Signal Table

| Error | Likely Cause | First Action |
|-------|-------------|-------------|
| `ENOLOCK` | Wrong working directory | `cd <repo-root>` |
| `isDescendantOf` null | npm workspace bug with deps | Manual install |
| `edgesOut` null | npm workspace bug with deps | Manual install |
| `EBADENGINE` | Node version mismatch | Check `node --version` vs package.json `engines` |
| Unchanged after `--force` | Sub-workspace still uses old dep | Check with `npm ls <pkg>` |
