---
name: kanban-system
description: "Hermes Kanban multi-agent collaboration system: orchestrator playbooks, worker pitfalls, and Codex integration lanes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, worker, collaboration, routing]
---

# Kanban System

Hermes Kanban is a durable SQLite work queue for multi-profile collaboration. This skill covers the orchestrator role, worker lifecycle, and optional Codex integration lanes.

---

## Orchestrator Playbook

The orchestrator's job is routing, not execution.

**Core rule: decompose, don't execute.**
- Break work into bite-sized tasks (2–5 min each).
- Assign tasks to the right profile.
- Review output, don't produce it.

**Lifecycle:**
1. **Decompose** — turn user requests into kanban tasks.
2. **Route** — assign to profiles via `kanban_create` or `kanban_assign`.
3. **Monitor** — tail task logs, watch for blocks.
4. **Reconcile** — merge worker output back into the main thread.
5. **Verify** — run tests / checks before marking complete.

**Anti-temptations:**
- Don't implement the task yourself.
- Don't skip verification.
- Don't let workers write durable Kanban state directly.

---

## Worker Lifecycle

Auto-injected into every dispatched worker's system prompt as `KANBAN_GUIDANCE`.

**6 steps:**
1. **Orient** — read task description, board state, and linked context.
2. **Work** — execute the task in `HERMES_KANBAN_WORKSPACE`.
3. **Heartbeat** — report progress every N minutes if running long.
4. **Block** — if stuck, call `kanban_block` with reason and needs.
5. **Complete** — call `kanban_complete` with output summary and artifacts.
6. **Handoff** — include exact paths, test results, and next steps.

**Workspace handling:**
- `scratch` — fresh tmp dir, read/write freely.
- `git` — existing repo, commit to feature branch.
- `docker` — isolated container.

**Good handoff shape:**
- What was done (one sentence)
- Exact file paths changed
- Test command + result
- Known issues / follow-ups

---

## Codex Integration Lane

Use Codex CLI as an isolated implementation lane while Hermes keeps ownership of task lifecycle.

**Rules:**
- Hermes decides whether Codex is appropriate.
- Hermes creates/selects the isolated workspace.
- Hermes starts and monitors Codex.
- Hermes reconciles diffs and runs verification.
- Codex output is not a task completion signal.

**Workflow:**
1. Check `kanban_show` to see if the task suits Codex (bounded, code-heavy).
2. Create/select a git worktree for isolation.
3. Start Codex: `tmux new-session -d -s codex 'codex'`
4. Send the task prompt via `tmux send-keys`.
5. Capture output, reconcile diff back to main workspace.
6. Run tests, write `kanban_complete` or `kanban_block`.

**Template:** `templates/kanban-codex-lane-prompt.md`
