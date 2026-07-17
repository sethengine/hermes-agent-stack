---
name: codex
description: Delegate coding tasks to OpenAI Codex CLI as a subprocess from OpenCode. Features, PR review, batch fixing.
---

# Codex CLI — Subprocess Orchestration from OpenCode

Delegate coding tasks to [Codex](https://github.com/openai/codex) (OpenAI's autonomous coding agent CLI) via bash subprocesses.

## Prerequisites

- **Install:** `npm install -g @openai/codex`
- **Auth:** Either `OPENAI_API_KEY` env var or Codex OAuth credentials from the Codex CLI login flow
- **Git repo required** — Codex refuses to run outside one
- **Check:** `codex --version`

## One-Shot Tasks

```bash
codex exec 'Add dark mode toggle to settings'
```

For scratch work (Codex needs a git repo):
```bash
cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

## Common Patterns

### Build a Feature

```bash
codex exec --full-auto 'Add user authentication with JWT tokens'
```

### Refactor Code

```bash
codex exec --full-auto 'Refactor the auth module to use dependency injection'
```

### PR Review

```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main
```

## Parallel Issue Fixing with Worktrees

```bash
# Create worktrees for isolation
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

# Launch Codex in each (they run independently)
cd /tmp/issue-78 && codex --yolo exec 'Fix issue #78: <description>. Commit when done.'
cd /tmp/issue-99 && codex --yolo exec 'Fix issue #99: <description>. Commit when done.'

# After completion, push and create PRs
cd /tmp/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'

# Cleanup
git worktree remove /tmp/issue-78
```

## Batch PR Reviews

```bash
# Fetch all PR refs
git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'

# Review multiple PRs in parallel
cd /project && codex exec 'Review PR #86. git diff origin/main...origin/pr/86'
cd /project && codex exec 'Review PR #87. git diff origin/main...origin/pr/87'

# Post results
gh pr comment 86 --body '<review-summary>'
```

## Rules

1. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch work.
2. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly.
3. **`--full-auto` for building** — auto-approves changes within the sandbox.
4. **`--yolo` for trusted work** — no sandbox, fastest execution.
5. **Parallel is fine** — run multiple Codex processes at once for batch work.
6. **Use git worktrees** — isolate parallel tasks to avoid file conflicts.
