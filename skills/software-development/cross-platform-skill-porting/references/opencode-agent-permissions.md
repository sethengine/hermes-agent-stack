# OpenCode Agent Permission Sets (v1.15.5)

Discovered from `opencode agent list` on a live v1.15.5 installation. OpenCode agents are permission-gated subagents configured in `~/.config/opencode/opencode.json`. These define what each agent type can do.

## Agent Types

| Agent | Role | Purpose |
|-------|------|---------|
| `build` | primary | Main code implementation agent with broad permissions |
| `plan` | primary | Planning agent, edit restricted to plan files only |
| `explore` | subagent | Read-only code exploration (grep, glob, list, bash, webfetch, websearch, read) |
| `general` | primary | General-purpose with broad access, todowrite denied |
| `summary` | primary | Read-only summary agent (all tools denied except search/read) |
| `compaction` | primary | Context compaction agent (all tools denied except search/read) |
| `title` | primary | Session titling agent (all tools denied except search/read) |
| `power` | all | Full access but search and crawl tools restricted |
| `simple` | all | Minimal toolset (no context7, brave-search, crawl, playwright, github) |

## Permission Model

Permissions are arrays of `{permission, action, pattern}` triples evaluated top-to-bottom:

```json
{
  "permission": "tool_name_or_category",
  "action": "allow|ask|deny",
  "pattern": "glob_pattern"
}
```

### Permission Categories

| Permission | Controls |
|-----------|----------|
| `*` | All permissions (catch-all) |
| `read` | File reading |
| `edit` | File editing |
| `write` | File creation |
| `bash` | Shell commands |
| `grep` | Content search |
| `glob` | File search by name |
| `list` | Directory listing |
| `webfetch` | Web page fetching |
| `websearch` | Web search |
| `crawl` | Web crawling |
| `searxng` | SearXNG search engine |
| `context7` | Context7 documentation lookup |
| `brave-search` | Brave Search API |
| `youtube-transcript` | YouTube transcript fetching |
| `c4ai` | C4AI tool |
| `playwright` | Browser automation |
| `github` | GitHub integration |
| `question` | Ask user questions |
| `plan_enter` | Enter plan mode |
| `plan_exit` | Exit plan mode |
| `repo_clone` | Clone repositories |
| `repo_overview` | Repository overview |
| `todowrite` | Task management |
| `doom_loop` | Loop detection |
| `external_directory` | Access paths outside project |

### External Directory Access

OpenCode restricts file access to the project directory by default. Access to external paths must be explicitly allowed:

```json
{
  "permission": "external_directory",
  "pattern": "/home/user/.local/share/opencode/tool-output/*",
  "action": "allow"
}
```

This is how graphify gets access to `~/.claude/skills/graphify/*` and `~/.config/opencode/skills/graphify/*`.

### Sensitive File Protection

OpenCode automatically protects `.env` and `.env.*` files (asks before reading), but allows `.env.example`:

```json
{"permission": "read", "pattern": "*.env", "action": "ask"},
{"permission": "read", "pattern": "*.env.*", "action": "ask"},
{"permission": "read", "pattern": "*.env.example", "action": "allow"}
```

## Build Agent (Primary — Full Access)

The build agent has the broadest permissions: `*` allowed, with specific restrictions on `doom_loop` (ask), `external_directory` (ask with exceptions), and `question`/`plan_enter`/`plan_exit`/`repo_clone`/`repo_overview` initially denied but overridden to allow later in the list. Search tools (searxng, context7, brave-search, youtube-transcript) are all allowed. `read` is allowed for everything except `.env` files.

Key: The permission list order matters — later entries override earlier ones. The build agent first denies `question`, `plan_enter`, `plan_exit`, then later allows `question` and `plan_enter` again. This pattern is intentional — it creates a base deny-then-allow structure.

## Plan Agent (Primary — Restricted Edit)

Same as build but:
- `edit` denied for everything (`"pattern": "*"`)
- `edit` allowed only for plan files: `.opencode/plans/*.md` and `~/.local/share/opencode/plans/*.md`
- `question` and `plan_exit` allowed
- `external_directory` allowed for plans directory

## Explore Agent (Subagent — Read-Only)

The explore agent is explicitly read-only:
- All permissions denied first (`"*"` → deny)
- Then selectively allows: `grep`, `glob`, `list`, `bash`, `webfetch`, `websearch`, `read`
- Search tools allowed (searxng, context7, brave-search, youtube-transcript)
- `external_directory` asks before accessing

## Power Agent — Restricted Search

Like build but:
- `searxng`, `context7`, `brave-search`, `youtube-transcript` → denied
- `crawl`, `c4ai`, `playwright` → denied
- `github` → allowed

## Simple Agent — Minimal Toolset

Like build but:
- `context7` → denied
- `brave-search` → denied
- `youtube-transcript` → denied
- `crawl` → denied
- `c4ai` → denied
- `playwright` → denied
- `github` → denied

## Skills Directory Access

The permission config reveals how OpenCode discovers skills:

```json
{
  "permission": "external_directory",
  "pattern": "/home/<user>/.claude/skills/graphify/*",
  "action": "allow"
},
{
  "permission": "external_directory",
  "pattern": "/home/<user>/.config/opencode/skills/graphify/*",
  "action": "allow"
}
```

This confirms:
1. Skills at `~/.config/opencode/skills/` are auto-discovered
2. Skills at `~/.claude/skills/` are also accessible (Claude Code compatibility)
3. Each skill directory needs explicit external_directory permission or must be under `~/.local/share/opencode/` or `/tmp/opencode/`

## Memory System

OpenCode stores persistent project memory at `~/.opencode/memory/project.md` in markdown with YAML frontmatter:

```yaml
---
description: ''
label: project
limit: 5000
read_only: false
---
```

The `limit` is 5000 characters. This is OpenCode's equivalent to Hermes' `memory` tool.
