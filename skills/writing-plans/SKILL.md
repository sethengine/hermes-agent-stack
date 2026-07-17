---
name: writing-plans
description: Write implementation plans with bite-sized tasks, exact paths, complete code, and verification steps. For delegation to subagents.
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:** "Build authentication system" (50 lines across 5 files)

**Right size:**
- "Create User model with email field" (10 lines, 1 file)
- "Add password hash field to User" (8 lines, 1 file)
- "Create password hashing utility" (15 lines, 1 file)

## Plan Document Structure

### Header (Required)

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

```markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

## Writing Process

### Step 1: Understand Requirements

Read and understand feature requirements, design documents, acceptance criteria, constraints.

### Step 2: Explore the Codebase

```bash
# Understand project structure
find src/ -name "*.py" | head -20

# Look at similar features
grep -rn "similar_pattern" src/ --include="*.py"

# Check existing tests
find tests/ -name "*.py" | head -20

# Read key files
cat src/app.py
```

### Step 3: Design Approach

Decide: architecture pattern, file organization, dependencies, testing strategy.

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)
**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)
**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

### TDD (Test-Driven Development)
Every task that produces code should include the full TDD cycle. See `test-driven-development` skill for details.

### Frequent Commits
Commit after every task: `git commit -m "type: description"`

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Vague tasks ("Add authentication") | Specific ("Create User model with email and password_hash fields") |
| Incomplete code ("Add validation function") | Include the complete function code |
| Missing verification ("Test it works") | Exact command with expected output |
| Missing file paths ("Create the model file") | Exact path ("Create: `src/models/user.py`") |

## Delegation Handoff

After saving the plan, use OpenCode's agent mentions to dispatch subagents:

```
@agent Implement Task 1 from the plan: [paste full task text with code, paths, commands]
@agent Implement Task 2 from the plan: [paste full task text]
```

Each subagent gets the complete task text in its context — never make subagents read the plan file.

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
