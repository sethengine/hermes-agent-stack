---
name: github-operations
description: "Complete GitHub workflow operations: auth, repositories, issues, PRs, code review, and codebase inspection."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, Pull-Requests, Issues, Repositories, Code-Review, CI/CD, Automation, Metrics]
---

# GitHub Operations

End-to-end guide for working with GitHub repositories, issues, pull requests, and code review. Each section shows the `gh` CLI way first, then the `git` + `curl` fallback for machines without `gh`.

---

## Prerequisites & Auth Detection

```bash
# Determine which method to use
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="curl"
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "^GITHUB_TOKEN=" ~/.hermes/.env 2>/dev/null; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\\\"\\n\\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Extract owner/repo from git remote
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

### Authentication Setup

**gh CLI (recommended):**
```bash
gh auth login        # Browser OAuth
gh auth status       # Verify
```

**Git-only (HTTPS token) — dual store for git + agent access:**
```bash
# Create token at https://github.com/settings/tokens (scopes: repo, workflow, read:org)
# Store in both places so both native git and curl-based tools can find it:
git config --global credential.helper store
echo "https://USER:TOKEN@github.com" > ~/.git-credentials
echo 'GITHUB_TOKEN="TOKEN"' >> ~/.hermes/.env
chmod 600 ~/.git-credentials ~/.hermes/.env
```

---

## Repository Management

### Clone / Create / Fork

```bash
# Clone
git clone https://github.com/owner/repo.git

# Create repo (gh)
gh repo create my-repo --public --description "A new repo"

# Fork (gh)
gh repo fork owner/repo --clone

# Fork (API)
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/forks
```

### Releases & Secrets

```bash
# Create release (gh)
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"

# Set secret (gh)
gh secret set API_KEY --body "secret-value"
```

---

## Issues Management

### View & Search

```bash
# With gh
gh issue list
gh issue list --state open --label "bug"
gh issue view 42

# With curl
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/issues?state=open&per_page=20" \
  | python3 -c "import sys,json; [print(f\"#{i['number']} {i['title']}\") for i in json.load(sys.stdin) if 'pull_request' not in i]"
```

### Create & Triage

```bash
# Create issue (gh)
gh issue create --title "Bug: login fails" --body "Steps to reproduce..." --label bug

# Add label (gh)
gh issue edit 42 --add-label "priority-high"

# Close (gh)
gh issue close 42 --reason "completed"
```

---

## Pull Request Workflow

### Branch & Commit

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/add-auth
# ... make changes ...
git add .
git commit -m "feat: add user authentication"
git push -u origin feat/add-auth
```

### Open PR

```bash
# With gh
gh pr create --title "feat: add user authentication" --body "Closes #42"

# With curl
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -d '{"title":"feat: add auth","head":"feat/add-auth","base":"main","body":"Closes #42"}' \
  "https://api.github.com/repos/$OWNER/$REPO/pulls"
```

### CI & Merge

```bash
gh pr checks 42          # View CI status
gh pr merge 42 --squash  # Merge with squash
```

---

## Code Review

### Review Local Changes (Pre-Push)

```bash
git diff --staged
git diff main...HEAD --stat
git log main..HEAD --oneline
```

### Review Open PRs

```bash
# View PR diff (gh)
gh pr diff 42

# View PR files (gh)
gh pr view 42 --json files

# Comment on PR (gh)
gh pr comment 42 --body "Consider adding a test for the edge case."
```

### Inline Comments via API

```bash
# Post review comment on a specific line
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -d '{"body":"This needs error handling.","commit_id":"abc123","path":"src/auth.py","position":5}' \
  "https://api.github.com/repos/$OWNER/$REPO/pulls/42/comments"
```

---

## Codebase Inspection

Analyze repository composition using `pygount`:

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount

pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox" \
  .
```

Filter by language:
```bash
pygount --suffix=py --format=summary .
```

---

## Remember

- Always check `gh auth status` before GitHub operations.
- Use `OWNER_REPO=$(git remote get-url origin | sed -E 's|.*github\.com[:/]||; s|\.git$||')` to extract owner/repo.
- `gh` is richer; `curl` + `git` works everywhere.
- Code review your own changes before pushing (`git diff main...HEAD`).
- Exclude dependency/build directories when running `pygount`.
