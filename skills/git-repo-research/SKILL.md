---
name: git-repo-research
description: "Internet research specialized for finding, analyzing, comparing, and evaluating GitHub/git repositories. Uses web search, web extraction, and GitHub API/GH CLI to produce repo intelligence."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, GitHub, Repositories, Analysis, Discovery, Open-Source, Comparison]
    related_skills: [research-assistant, github-operations, subagent-driven-development]
---

# Git Repo Research

Research GitHub repositories through internet search: find, analyze, compare, and evaluate open-source projects. This skill covers the full pipeline from initial discovery to synthesized report.

---

## Workflow Overview

```
1. DISCOVER → Find candidate repos via web search
2. ANALYZE   → Read READMEs, codebase structure, docs
3. QUALIFY   → Assess activity, community, quality signals
4. COMPARE   → Side-by-side evaluation across repos
5. SYNTHESIZE → Output a structured research report
```

---

## 1. DISCOVER — Find Repos

### Web Search Patterns

Search GitHub directly or the wider web for repos:

```python
# Search GitHub repos by topic
web_search("github.com awesome-list LLM agent framework 2025")

# Search by tech stack
web_search("github.com vector database written in rust")

# Search by problem domain
web_search("site:github.com RAG knowledge base retrieval augmented generation")

# Search for alternatives
web_search("alternatives to langchain open source 2025")

# Search by criteria
web_search("github.com MQTT broker high performance stars:>1000")
```

### GitHub Topics Search

GitHub topic pages are curated — use them for high-quality discovery:

```python
web_search("github.com/topics/vector-database")
web_search("github.com/topics/agent-framework python")
```

### Awesome Lists

Great starting points for curated comparisons:

```python
web_search("github.com awesome LLMOps tools")
web_search("github.com awesome MLOps 2025")
web_search("github.com/owner/awesome-list")  # then web_extract README.md
```

---

## 2. ANALYZE — Read a Repo

### README Analysis (Non-Interactive)

GitHub serves raw files at `raw.githubusercontent.com` — fast, no browser needed:

```python
web_extract("https://raw.githubusercontent.com/owner/repo/main/README.md")
```

For longer content, use paginated reads:

```python
# First page
web_extract("https://github.com/owner/repo")
```

### Repo Metadata via GitHub API

Fast, structured JSON — no parsing HTML:

```bash
curl -s "https://api.github.com/repos/owner/repo" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"Stars: {d['stargazers_count']}")
print(f\"Forks: {d['forks_count']}")
print(f\"Open Issues: {d['open_issues_count']}")
print(f\"Last Push: {d['pushed_at']}")
print(f\"Created: {d['created_at']}")
print(f\"License: {d.get('license', {}).get('spdx_id', 'N/A')}")
print(f\"Topics: {', '.join(d.get('topics', []))}")
print(f\"Language: {d['language']}")
print(f\"Description: {d['description']}")
print(f\"Default Branch: {d['default_branch']}")
print(f\"Has Wiki: {d['has_wiki']}")
print(f\"Has Pages: {d['has_pages']}")
"
```

### Analyze Codebase Structure

When you need to understand a repo's internals:

```python
# Clone and inspect
terminal("git clone --depth 1 https://github.com/owner/repo.git /tmp/repo-snapshot")
terminal("ls -la /tmp/repo-snapshot")
terminal("ls /tmp/repo-snapshot/src")
terminal("ls /tmp/repo-snapshot/docs")
```

Or use GitHub API for tree view without cloning:

```bash
curl -s "https://api.github.com/repos/owner/repo/git/trees/main?recursive=1" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('tree', []):
    print(f\"{item['type']:4s} {item['path']}\")
" | head -80
```

### Recent Activity

```bash
# Recent commits (via API)
curl -s "https://api.github.com/repos/owner/repo/commits?per_page=10" \
  | python3 -c "
import sys, json
commits = json.load(sys.stdin)
for c in commits:
    sha = c['sha'][:7]
    msg = c['commit']['message'].split('\n')[0]
    date = c['commit']['committer']['date'][:10]
    author = c['commit']['author']['name']
    print(f'{date} {sha} {author}: {msg}')
"

# Recent releases
curl -s "https://api.github.com/repos/owner/repo/releases?per_page=5" \
  | python3 -c "
import sys, json
releases = json.load(sys.stdin)
for r in releases:
    print(f\"{r['tag_name']:20s} {r['published_at'][:10]} {r['name']}\")
"
```

---

## 3. QUALIFY — Assess Repo Health

Use these signals to rate a repo's quality:

### Activity Signals

| Signal | Good | Concerning | Dead |
|--------|------|-----------|------|
| Last commit | < 3 months | 3-12 months | > 12 months |
| Commit frequency | Daily/weekly | Monthly | > quarterly |
| Recent release | < 6 months | 6-12 months | > 12 months |
| Response to issues | Days | Weeks | No response |

### Quality Signals

| Signal | Good | Concerning |
|--------|------|------------|
| Stars | High for niche | Suspiciously high for new repo |
| Documentation | README + docs site + examples | README only, sparse |
| Tests | CI + coverage badge | No tests visible |
| Contributing | CONTRIBUTING.md + CODE_OF_CONDUCT | None |
| License | OSI-approved | None (red flag) |
| Issues | Active triage, labels | 100+ unaddressed |
| CI/CD | CI badges passing | No CI |

### Quick Health Check Script

Save this as a reusable script:

```bash
#!/usr/bin/env bash
# Usage: check-repo.sh owner/repo
REPO="$1"
[ -z "$REPO" ] && echo "Usage: $0 owner/repo" && exit 1

echo "=== Repo: $REPO ==="
DATA=$(curl -s "https://api.github.com/repos/$REPO")

# Basic info
echo "Stars:     $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('stargazers_count','?'))")"
echo "Forks:     $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('forks_count','?'))")"
echo "License:   $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('license',{}).get('spdx_id','N/A') if d.get('license') else 'None')")"
echo "Language:  $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('language','?'))")"
echo "Created:   $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('created_at','?')[:10])")"
echo "Updated:   $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('updated_at','?')[:10])")"
echo "Last Push: $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pushed_at','?')[:10])")"
echo "Open Issues: $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('open_issues_count','?'))")"
echo "Topics:    $(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(', '.join(d.get('topics',[])))")"
```

---

## 4. COMPARE — Multiple Repos Side by Side

### Comparison Template

Use web_search to discover candidates first, then run the health check across all:

```python
repos = ["owner/repo-a", "owner/repo-b", "owner/repo-c"]

for repo in repos:
    # Fetch and display key metrics
    data = terminal(f"curl -s https://api.github.com/repos/{repo}")
    # Parse and format as table rows
```

### Comparison Matrix

| Criteria | Repo A | Repo B | Repo C |
|----------|--------|--------|--------|
| Stars | | | |
| Last commit | | | |
| Language | | | |
| License | | | |
| Has docs? | | | |
| Has tests? | | | |
| Active maintainer? | | | |
| Your need match | | | |

### Multi-Repo Research via Subagents

For large comparisons (5+ repos), parallelize with `delegate_task`:

```python
delegate_task(
    goal="Research Repo X",
    context=f"""
    Research this repo: https://github.com/owner/repo-x
    
    1. Get repo metadata (stars, forks, license, last push, language)
    2. Read the README and summarize what it does
    3. Check recent commits and release history
    4. Note any red flags (no license, stale, no docs)
    
    Return a structured summary.
    """,
    toolsets=['terminal', 'web']
)
```

---

## 5. SYNTHESIZE — Output a Research Report

### Standard Report Structure

```markdown
# Repo Research: [Topic/Query]

## Summary
[One-paragraph synthesis of findings]

## Candidate Repos

### 1. [repo-name] ⭐⭐⭐
**URL:** https://github.com/owner/repo
**Stars:** X | **Language:** Y | **License:** Z | **Last push:** Date
**What it does:** [1-2 sentences]
**Strong points:** [key strengths]
**Weak points:** [key weaknesses]
**Best for:** [specific use case it fits]

### 2. [repo-name] ⭐⭐
...

## Comparison Table

| Criteria | Repo A | Repo B | Repo C |
|----------|--------|--------|--------|
| Stars | | | |
| Maturity | | | |
| Docs quality | | | |
| Community | | | |
| Your fit | | | |

## Recommendation
[Which repo to use and why. Or a verdict like "none mature enough, wait for X".]
```

---

## Example: Full Research Session

Here's a complete example researching "best open-source RAG framework" in Python:

```python
from hermes_tools import web_search, web_extract, terminal

# Step 1: Discover
results = web_search("best open source RAG framework Python 2025 github")

# Step 2: Get shortlist from search results
# (extract repo URLs from web_search results)

# Step 3: Analyze each candidate
repos = ["run-llama/llama_index", "langchain-ai/langchain", "chatchat-space/Langchain-Chatchat"]
for repo in repos:
    meta = terminal(f"curl -s https://api.github.com/repos/{repo}")
    readme = web_extract(f"https://raw.githubusercontent.com/{repo}/main/README.md")

# Step 4: Compare and recommend
# Build the comparison table in Python and output as Markdown
```

---

## Pro Tips

- **Rate limits**: Unauthenticated GitHub API = 60 req/hr. Set `GITHUB_TOKEN` for 5000 req/hr.
- **RAW GitHub URLs**: Use `raw.githubusercontent.com/owner/repo/branch/path` instead of browser for READMEs and docs — faster, no JS.
- **Stars aren't everything**: A 500-star repo with active commits can be better than a 10K-star abandoned one.
- **Check the issue tracker**: Open vs closed ratio tells you about maintenance. So does stale bot config.
- **Check the CONTRIBUTORS file**: Single maintainer = bus factor risk. Active community = healthier.
- **Forks comparison**: Top forks sometimes surpass the original. Check both.
- **Use `gh` CLI**: If `gh` is installed, `gh repo view owner/repo --json ...` is faster than curl.
- **Parallelize comparisons**: Use `delegate_task` to research repos in parallel. Each subagent works independently.

## Red Flags — Watch For

- No license file → can't use it in your project legally
- Last commit > 1 year ago → likely abandoned (unless declared stable)
- Single commit / no tags → experimental, not production-ready
- README is a stub → poor documentation culture
- No CI / no tests → quality unknown
- Lots of emoji-burst marketing → could be vaporware
- Many open issues with no responses → maintainer unresponsive
- No releases/packages → more work to integrate

## Related Skills

- **research-assistant** — For general internet research (papers, blogs, wikis)
- **github-operations** — When you need to actually clone, create PRs, or manage repos
- **subagent-driven-development** — For dispatching parallel research subagents
- **writing-plans** — For turning research findings into implementation plans
