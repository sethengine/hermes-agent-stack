---
name: self-review
description: Post-task self-improvement review — save durable lessons to memory and skills after complex tasks, user corrections, or session milestones. Mirror of Hermes background review loop.
trigger: /review
---

# Self-Review Protocol

After complex tasks, user corrections, or session milestones, review the
conversation and update two things: **memory** (who the user is and what
the environment is) and **skills** (how to do this class of task).

## Step 1: Review Memory

Scan the conversation for:

- User persona, preferences, personal details, environment changes
- Behavioral expectations, work style, communication preferences
- Durable facts that will still matter in 7+ days

If found: use the `memory` tool to save a compact declarative fact.

**Never save:** task progress, PR numbers, issue numbers, commit SHAs,
session artifacts, or anything stale in a week.

If nothing durable: skip.

## Step 2: Review Skills

Be ACTIVE — most sessions produce at least one skill update. A pass that
does nothing is a missed learning opportunity, not a neutral outcome.

**Signals that warrant a skill update (any one is enough):**

- User corrected your style, tone, format, legibility, verbosity, or approach. Frustration is a first-class skill signal — "stop doing X", "don't format like this", "I hate when you Y" — embed the lesson in the skill that governs that task so the next session starts fixed.
- Non-trivial technique, fix, workaround, or debugging path emerged.
- A skill that was loaded or consulted turned out wrong, missing, or outdated — patch it now.

**Preference order — pick the earliest that fits:**

1. **PATCH A LOADED SKILL** — if a skill was loaded (`/skill-name` or `skill_view`) and covers the learning, patch it first. It was in play.
2. **PATCH AN EXISTING UMBRELLA** — use `skill_manage(action='patch')` to add a subsection, pitfall, or broaden a trigger in the skill that governs this task class.
3. **ADD A SUPPORT FILE** — `skill_manage(action='write_file')` under an existing umbrella skill. Three kinds:
   - `references/<topic>.md` — session-specific detail (error transcripts, reproduction recipes, provider quirks) OR condensed knowledge banks (quoted research, API docs excerpts, domain notes) written concise and task-focused.
   - `templates/<name>.<ext>` — starter files meant to be copied and modified.
   - `scripts/<name>.<ext>` — statically re-runnable actions (verification, fixture generators, probes).
   Add a one-line pointer in the umbrella's SKILL.md so future agents find them.
4. **CREATE A NEW CLASS-LEVEL SKILL** — `skill_manage(action='create')` when no existing skill covers the class. Name at the class level — NOT a PR number, error string, codename, library-alone name, or "fix-X"/"debug-Y" session artifact. If the proposed name only makes sense for today's task, fall back to (1), (2), or (3).

**User-preference embedding:** when the user complained about how you handled a task, update the relevant skill — memory alone isn't enough. Memory says "who the user is and the current situation"; skills say "how to do this class of task for this user". Both should carry user-preference lessons when relevant.

**Protected skills** (bundled + hub-installed): do NOT edit.

**Pinned skills** (marked via `hermes curator pin`): CAN be improved — pin only blocks deletion/archive, not content updates.

If you notice two existing skills overlapping, mention it — the background curator handles consolidation.

## Step 3: Declare

- Memory saved → emit `💾 Memory updated: <what>`
- Skill updated → emit `📚 Skill updated: <what>`
- If nothing worth saving → say nothing and move on

## Pitfalls

- Do NOT capture environment-dependent failures as permanent rules (missing binaries, fresh-install errors, "command not found" — the user can fix these, they are not durable rules)
- Do NOT capture negative claims about tools or features ("browser does not work", "X tool is broken") — these harden into refusals the agent cites against itself for months after the actual problem was fixed
- Do NOT capture session-specific transient errors that resolved before the conversation ended. If retrying worked, the lesson is the retry pattern, not the original failure.
- Do NOT capture one-off task narratives. "Summarize today's market" is not a class of work warranting a skill.
- Memory = facts about user + environment. Skills = procedures and workflows.
- Write memories as declarative facts ("User prefers concise responses"), not instructions ("Always respond concisely")
- If nothing to save, say "Nothing to save" — it's a valid outcome, just not the default
