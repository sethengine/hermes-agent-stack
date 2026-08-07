---
source: "20260720_220749_3185a0"
date: "2026-07-20"
category: software
wiki-links: [hermes_system_prompt_management, diablo_2_resurrected_community_fixes]
---

# Hermes Skill Pruning (`hermes skills prune`)

Stale skills bloat the session search index and pollute context. Prune them with:

```bash
hermes skills prune --threshold 90d --confidence 0.5
```

## Flags

- **`--threshold 90d`** — Days since last use. Skills untouched past this become candidates. Valid: `30d`, `60d`, `180d` etc.
- **`--confidence 0.5`** — Minimum confidence score floor. Skills below this are pruned.

## How tracking works

`hermes skills analyze` shows usage stats:

| Skill | Uses | Last Used | Confidence |
|---|---|---|---|
| fetch_report | 45 | 2 days ago | 98% |
| old_query | 1 | 120 days ago | 23% |

## Learning loop auto-recreates

Pruning does not lose capability — the learning loop regenerates skills on demand (5-tool-call rule). A regenerated skill is often better because user preferences have evolved. Rollback: `hermes skills restore`.
