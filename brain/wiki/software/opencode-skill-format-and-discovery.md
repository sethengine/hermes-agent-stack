---
source_session: 20260521_145657_60b2c4
date: 2026-05-21
category: software
tags: [opencode, skills, skill-porting, claude-code, agents]
---

# OpenCode Skill Format & Discovery

OpenCode discovers skills from `~/.config/opencode/skills/<name>/SKILL.md` (user-level), `~/.claude/skills/<name>/SKILL.md` (shared with Claude Code), and `.opencode/` (per-project). Format is simpler than Hermes: YAML frontmatter `name`, `description`, optional `trigger` (creates a slash command like `/arxiv`).

Separate from skills: the `agents` system — permission-gated subagents (`build`, `plan`, `explore`, `general`, `power`, `simple`) configured in `opencode.json`.

**Porting Hermes skills → OpenCode tool mapping:** `read_file`→`cat`/`read`, `search_files`→`grep`/`find`, `delegate_task`→`@agent` mentions, `web_extract`→`webfetch`, `terminal`→`bash`. Skip Hermes-specific skills (e.g. hermes-agent) unless spawning Hermes as a subprocess.

**Adapted set (10):** arxiv, llm-wiki, blogwatcher, systematic-debugging, test-driven-development, writing-plans, subagent-driven-development, claude-code, codex, opencode.

[[opencode-prompt-architecture]] [[hermes-opencode-skills-repos]] [[cross-platform-skill-porting]]
