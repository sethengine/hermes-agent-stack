---
name: subagent-driven-development
description: Execute implementation plans by dispatching fresh subagents per task with two-stage review (spec compliance then code quality).
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

- You have an implementation plan (from writing-plans skill)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text upfront:

```bash
cat docs/plans/feature-plan.md
```

Parse out each task — you'll provide the complete task text to each subagent.

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide full task text directly.

### 2. Per-Task Workflow (using OpenCode @agent mentions)

For EACH task:

#### Step 1: Dispatch Implementer Subagent

```
@agent Implement Task 1: [paste full task text with file paths, code, commands]
Make sure to follow TDD:
1. Write failing test first
2. Verify it fails
3. Write minimal code
4. Verify it passes
5. Commit
```

#### Step 2: Dispatch Spec Compliance Reviewer

```
@agent Review if the implementation matches the spec. 
Check against these requirements:
- [list each requirement from the plan]
- Did they implement exactly what was specified?
- Nothing extra added?
- Output: PASS or list of specific gaps.
```

**If spec issues found:** Fix gaps, re-review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

```
@agent Review code quality for the implementation.
Check:
- Follows project conventions?
- Proper error handling?
- Clear names?
- Adequate tests?
- No bugs or missed edge cases?
- No security issues?
Output: CRITICAL / IMPORTANT / MINOR issues with verdict APPROVED or REQUEST_CHANGES.
```

**If quality issues found:** Fix, re-review. Continue only when approved.

#### Step 4: Mark Complete and Continue

### 3. Final Integration Review

After ALL tasks complete:

```
@agent Review the entire implementation for consistency:
- Do all components work together?
- Any inconsistencies between tasks?
- All tests passing?
- Ready for merge?
```

### 4. Final Verification

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:** "Implement user authentication system"
**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"

## Red Flags — Never Do These

- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Accept "close enough" on spec compliance
- Let implementer self-review replace actual review
- Start code quality review before spec compliance is PASS
- Move to next task while either review has open issues

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

## Integration with Other Skills

- **writing-plans** — creates the plan; this skill executes it
- **test-driven-development** — implementer subagents should follow TDD
- **systematic-debugging** — if subagent hits bugs, follow systematic debugging process

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Extract 5 tasks]

--- Task 1: Create User model ---
@agent Implement Task 1: Create src/models/user.py with User class...
  Agent: Implemented, 3/3 tests passing, committed.

@agent Review Task 1 spec compliance: does it match plan?
  Agent: PASS — all requirements met

@agent Review Task 1 code quality
  Agent: APPROVED — clean code, good tests

--- Task 2: Password hashing ---
@agent Implement Task 2: Add password hashing utility...
  Agent: No questions, implemented, 5/5 tests passing.

@agent Review Task 2 spec compliance
  Agent: FAIL — missing password strength validation (spec says "min 8 chars")

@agent Fix the missing validation
  Agent: Added validation, 7/7 tests passing.

@agent Review Task 2 spec compliance (re-review)
  Agent: PASS

@agent Review Task 2 code quality
  Agent: Important: Magic number 8, extract to constant
  (Fix, re-review: APPROVED)

... (continue for all tasks)

@agent Final integration review
[Run full test suite: all passing]
[Done!]
```

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**
