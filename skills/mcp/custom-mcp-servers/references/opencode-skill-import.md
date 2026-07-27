# OpenCode: Importing Skills from Hermes / Other Sources

When copying skills from Hermes to OpenCode, important behavioral details can cause skills to not appear. This reference captures what was learned during a bulk import of ~95 Hermes skills.

## Critical: Symlinks Are NOT Followed for Skill Discovery

OpenCode discovers skills by scanning its skills directory (`~/.config/opencode/skills/`). It does NOT follow symlinks. A symlinked skill directory will not appear in the skill list.

**Correct approach — copy the real directory:**
```bash
cp -r ~/.hermes/skills/last30days ~/.config/opencode/skills/last30days
```

**Incorrect approach — symlinking:**
```bash
ln -s ~/.hermes/skills/last30days ~/.config/opencode/skills/last30days  # BROKEN
```

## Symlink Chain Resolution

Hermes skills themselves may be symlinks to another canonical location. For example, on this system:
```
~/.config/opencode/skills/last30days → ~/.hermes/skills/last30days → ~/.agents/skills/last30days
```

Both levels of symlinks must be resolved when copying. Use `readlink -f` to follow the full chain and identify the real source directory:

```bash
REAL_SOURCE=$(readlink -f ~/.hermes/skills/last30days)
cp -r "$REAL_SOURCE" ~/.config/opencode/skills/last30days
```

## Full Bulk Import Script

```bash
# Copy all Hermes skills to OpenCode as real directories
for f in ~/.hermes/skills/*/SKILL.md; do
    dir=$(dirname "$f")
    name=$(basename "$dir")
    # Resolve symlinks
    real=$(readlink -f "$dir")
    # Copy if not already present
    if [ ! -d ~/.config/opencode/skills/"$name" ]; then
        cp -r "$real" ~/.config/opencode/skills/"$name"
        echo "Imported: $name"
    fi
done
```

## SKILL.md Format Compatibility

OpenCode recognizes skills by their frontmatter `name:` field. The format is:

```
---
name: skill-name
description: Short description of what the skill does
---
```

Hermes skills use the same frontmatter format (with optional additional fields like `version`, `author`, `license`, `metadata`). OpenCode ignores extra frontmatter fields — they're compatible as-is. No format conversion needed.

## Restart Required

Skills are discovered at startup. After copying new skills into `~/.config/opencode/skills/`, OpenCode must be restarted for them to appear.
