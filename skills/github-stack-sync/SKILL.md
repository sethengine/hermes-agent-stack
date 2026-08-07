---
name: github-stack-sync
description: Sync Hermes agent stack (configs, skills, MCP bridge, dialogue) to a GitHub repository. Run after making changes to keep the backup fresh.
argument-hint: 'github-stack-sync | github-stack-sync skills | github-stack-sync configs'
user-invocable: true
---

# GitHub Stack Sync

Sync your entire Hermes/OpenCode agent stack to a GitHub repository. One command to snapshot configs, skills, MCP bridge code, and session history.

## Quick Run

```
/github-stack-sync
```

Syncs everything. For partial syncs:

- `/github-stack-sync configs` — only config files
- `/github-stack-sync skills` — only skills
- `/github-stack-sync bridge` — only the MCP bridge
- `/github-stack-sync sessions` — only session history

## What gets synced

| Source | Destination in repo |
|---|---|
| `~/.hermes/config.yaml` | `configs/hermes/default-config.yaml` |
| `~/.hermes/profiles/*/config.yaml` | `configs/hermes/{profile}-config.yaml` |
| `~/.config/opencode/opencode.json` | `configs/opencode/opencode.json` |
| `~/searxng/config/settings.yml` | `configs/searxng/settings.yml` |
| `~/.local/bin/mcp-bridge` | `mcp-bridge/mcp-bridge` |
| `~/.local/bin/searxng-mcp` | `mcp-bridge/searxng-mcp` |
| `~/.hermes/skills/*/` | `skills/` (all SKILL.md + references/scripts) |
| `~/.hermes/sessions/` (recent) | `sessions/` (last 5 session JSONs) |
| `~/.dotfiles/` (via `backup.sh`) | `system/` mirror — latency-tuning root files (cpu0 HWP fix, IRQ pin, prio guard) |

## How it works

1. Copies all live files into `~/.config/.src/hermes-stack/`
2. **Chains `dotfile-backup`** in `all` mode — mirrors the system latency-tuning files (`/lib`, `/etc`, `/usr/local/bin`) into the dotfiles `system/` tree and commits them too
3. Redacts API tokens/keys automatically (GitHub PATs, API keys)
4. Commits with a timestamp
5. Pushes to `https://github.com/sethengine/hermes-agent-stack`

## Usage (agents)

Run the script directly — do NOT inline the code from this doc:

```bash
bash ~/.hermes/skills/github-stack-sync/scripts/sync.sh            # all (configs+skills+bridge+sessions+dotfiles)
bash ~/.hermes/skills/github-stack-sync/scripts/sync.sh configs   # configs only
bash ~/.hermes/skills/github-stack-sync/scripts/sync.sh skills    # skills only
bash ~/.hermes/skills/github-stack-sync/scripts/sync.sh dotfiles  # dotfile-backup only
```

> The logic lives in `scripts/sync.sh` (bash). Edit that file, not this doc.

## Notes

- GitHub token must be in `~/.hermes/config.yaml` as `GITHUB_PERSONAL_ACCESS_TOKEN`
- The repo at `~/.config/.src/hermes-stack` must already be cloned and initialized
- All secrets are redacted before push — the public repo never sees your API keys
- Session history may contain private conversation data — review before syncing
- `dotfiles` mode requires `~/.dotfiles/backup.sh` present (installs via the dotfile-backup skill)

## Cron setup (optional)

To auto-sync daily, add to `~/.hermes/cron/` or use Hermes cron:

```bash
hermes cron create --name "github-stack-sync" --schedule "0 4 * * *" \
  --prompt "Run the github-stack-sync skill (bash ~/.hermes/skills/github-stack-sync/scripts/sync.sh) to back up all configs, skills, and dotfiles to GitHub."
```

## Notes

- GitHub token must be in `~/.hermes/config.yaml` as `GITHUB_PERSONAL_ACCESS_TOKEN` (env section or under github MCP server)
- The repo at `~/.config/.src/hermes-stack` must already be cloned and initialized
- All secrets are redacted before push — the public repo never sees your API keys
- Session history may contain private conversation data — review before syncing
