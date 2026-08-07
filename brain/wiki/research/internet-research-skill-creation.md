---
source_session: 20260603_233440_8b6f9b
date: 2026-06-03
category: research
tags: [internet-research, skill, hermes, templates, scripts]
---

# Internet-Research Skill Creation

The `internet-research` skill was built at `research/internet-research/` (7 files) as a full-spectrum research lifecycle for Hermes.

## SKILL.md — 10 Sections

1. **Methodology** — Frame → Search → Extract → Evaluate → Synthesize → Gap-check loop; framing questions scope any research
2. **Search Strategy** — 12 `web_search` operators, query templates by goal, always 3+ search angles
3. **Source Types** — credibility pyramid (peer-reviewed → social media); browser vs `web_extract` decision table
4. **Fact-Checking** — CRAAP test, cross-reference protocol, claim decomposition, number verification
5. **Deep Research** — citation chaining, lateral searching, Wikipedia pipeline, parallel subagents, temporal analysis, Wayback Machine
6. **Domain-Specific** — patterns for tech, people, companies, news, health, legal
7. **Synthesis** — quick-fact format, structured report template, comparison matrices
8. **Pitfalls** — 7 common mistakes with fixes; red/green-flag source guides
9-10. Resources — templates + scripts

## Templates & Scripts

- Templates: `research-brief-template.md`, `source-log-template.md`, `synthesis-report-template.md`
- Scripts: `source-credibility-check.py` (🟢/🟡/🟠/🔴 URL classification), `multi-angle-search.py` (4 angles), `temporal-analysis.py` (year-by-year timelines)

## Skill Relationships

Parent of `git-repo-research`; sibling of `research-assistant`; feeds `writing-plans`. Load via `skill_view('internet-research')`.

See also: [[git-repo-research-skill]], [[opencode-research-agent-setup]], [[research-skill-landscape]]
