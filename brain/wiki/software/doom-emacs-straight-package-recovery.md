---
source_session: "20260704_175147_58c619"
category: software
date: "2026-07-04"
---

# straight.el Package Repository Recovery

## Problem
When `doom sync` times out or is interrupted, `straight.el` repos under `~/.local/share/straight/repos/` can be left in a half-cloned state. Common symptoms:
- "Cannot read working tree" errors
- Empty cloned directories
- Stuck git processes

## Fix
1. **Check for bad repos** — look for tiny/empty directories:
   ```bash
   du -sh ~/.local/share/straight/repos/*/ | sort -h | head
   ```
2. **Remove bad repos** — delete directories with suspiciously small sizes (e.g., `4.0K`) and re-run `doom sync`:
   ```bash
   rm -rf ~/.local/share/straight/repos/bad-repo-name
   ```
3. **Also check packages that use separate repos** — e.g., small CL packages like `nose` (not `nose.el`) that have empty clone directories

## Bulk cleanup
```bash
# Find and nuke all repos with 4.0K or 8.0K directories (empty clones)
du -sh ~/.local/share/straight/repos/*/ | awk '$1 ~ /^[48]\.0K$/' | cut -f2- | xargs rm -rf
doom sync
```

## Prevention
- Don't enable too many modules at once (60+ lang modules in one `doom sync` is risky)
- Run `doom sync` with ample timeout
- If a module is not needed, keep it commented out

## Related
- [[doom-emacs-ide-setup]]
