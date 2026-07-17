---
name: llm-wiki
description: Build and query an interlinked markdown knowledge base. Based on Karpathy's LLM Wiki pattern — knowledge compounds over time instead of being rediscovered per query.
trigger: /wiki
---

# Karpathy's LLM Wiki

Build and maintain a persistent, compounding knowledge base as interlinked markdown files.
Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Unlike traditional RAG (which rediscovers knowledge from scratch per query), the wiki
compiles knowledge once and keeps it current. Cross-references are already there.
Contradictions have already been flagged. Synthesis reflects everything ingested.

**Division of labor:** The human curates sources and directs analysis. The agent
summarizes, cross-references, files, and maintains consistency.

## When This Skill Activates

Use this skill when the user:
- Asks to create, build, or start a wiki or knowledge base
- Asks to ingest, add, or process a source into their wiki
- Asks a question and an existing wiki is present
- Asks to lint, audit, or health-check their wiki
- References their wiki, knowledge base, or "notes" in a research context

## Wiki Location

**Default:** `~/wiki`

Set a custom location: `WIKI_PATH=~/my-knowledge-base` (in your environment or config).

## Architecture: Three Layers

```
wiki/
├── SCHEMA.md           # Conventions, structure rules, domain config
├── index.md            # Sectioned content catalog with one-line summaries
├── log.md              # Chronological action log (append-only, rotated yearly)
├── raw/                # Layer 1: Immutable source material
│   ├── articles/       # Web articles, clippings
│   ├── papers/         # PDFs, arxiv papers
│   ├── transcripts/    # Meeting notes, interviews
│   └── assets/         # Images, diagrams referenced by sources
├── entities/           # Layer 2: Entity pages (people, orgs, products, models)
├── concepts/           # Layer 2: Concept/topic pages
├── comparisons/        # Layer 2: Side-by-side analyses
└── queries/            # Layer 2: Filed query results worth keeping
```

**Layer 1 — Raw Sources:** Immutable. The agent reads but never modifies these.
**Layer 2 — The Wiki:** Agent-owned markdown files. Created, updated, and cross-referenced by the agent.
**Layer 3 — The Schema:** `SCHEMA.md` defines structure, conventions, and tag taxonomy.

## Resuming an Existing Wiki (CRITICAL — do this every session)

When the user has an existing wiki, **always orient yourself before doing anything**:

1. **Read `SCHEMA.md`** — understand the domain, conventions, and tag taxonomy.
2. **Read `index.md`** — learn what pages exist and their summaries.
3. **Scan recent `log.md`** — read the last 20-30 entries to understand recent activity.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
cat "$WIKI/SCHEMA.md"
cat "$WIKI/index.md"
tail -30 "$WIKI/log.md"
```

Only after orientation should you ingest, query, or lint. This prevents:
- Creating duplicate pages for entities that already exist
- Missing cross-references to existing content
- Contradicting the schema's conventions
- Repeating work already logged

For large wikis (100+ pages), also run a quick `grep` for the topic at hand before creating anything new.

## Initializing a New Wiki

When the user asks to create or start a wiki:

1. Determine the wiki path (from `$WIKI_PATH` env var, or ask the user; default `~/wiki`)
2. Create the directory structure above
3. Ask the user what domain the wiki covers — be specific
4. Write `SCHEMA.md` customized to the domain
5. Write initial `index.md` with sectioned header
6. Write initial `log.md` with creation entry
7. Confirm the wiki is ready and suggest first sources to ingest

### SCHEMA.md Template

```markdown
# Wiki Schema

## Domain
[What this wiki covers]

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages that synthesize 3+ sources, append `^[raw/articles/source-file.md]` at the end of paragraphs whose claims come from a specific source.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true                        # set when the page has unresolved contradictions
contradictions: [other-page-slug]      # pages this one conflicts with
---
```

### raw/ Frontmatter

Raw sources also get frontmatter for drift detection:

```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

The `sha256:` lets a future re-ingest of the same URL skip processing when content is unchanged.

## Tag Taxonomy
[Define 10-20 top-level tags for the domain. Add new tags here BEFORE using them.]

Example for AI/ML:
- Models: model, architecture, benchmark, training
- People/Orgs: person, company, lab, open-source
- Techniques: optimization, fine-tuning, inference, alignment, data
- Meta: comparison, timeline, controversy, prediction

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions or minor details
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`, remove from index

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
```

### index.md Template

```markdown
# Wiki Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->

## Concepts

## Comparisons

## Queries
```

### log.md Template

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [domain]
- Structure created with SCHEMA.md, index.md, log.md
```

## Core Operations

### 1. Ingest

When the user provides a source (URL, file, paste), integrate it into the wiki:

1. **Capture the raw source:**
   - URL → use `webfetch` to get markdown, save to `raw/articles/`
   - PDF → use `webfetch` (handles PDFs), save to `raw/papers/`
   - Pasted text → save to appropriate `raw/` subdirectory
   - Add raw frontmatter (`source_url`, `ingested`, `sha256`)

2. **Discuss takeaways** with the user — what's interesting, what matters for the domain.

3. **Check what already exists** — grep index.md and search for existing pages for mentioned entities/concepts.

4. **Write or update wiki pages:**
   - Create pages only if they meet the Page Thresholds
   - Add new information to existing pages, bump `updated` date
   - Cross-reference: every new page must link to at least 2 other pages
   - Tags: only use tags from the taxonomy in SCHEMA.md
   - Provenance markers for pages synthesizing 3+ sources

5. **Update navigation:**
   - Add new pages to `index.md` alphabetically under the correct section
   - Update "Total pages" count and "Last updated" date
   - Append to `log.md`

6. **Report what changed** — list every file created or updated.

### 2. Query

When the user asks a question about the wiki's domain:

1. **Read `index.md`** to identify relevant pages.
2. **For large wikis**, also `grep` across all `.md` files for key terms.
3. **Read the relevant pages**.
4. **Synthesize an answer** from the compiled knowledge. Cite the wiki pages you drew from.
5. **File valuable answers back** — create a page in `queries/` or `comparisons/` for substantial syntheses.
6. **Update log.md** with the query.

### 3. Lint

When the user asks to lint or health-check the wiki:

1. **Orphan pages:** Find pages with no inbound `[[wikilinks]]`. Use grep to build the inbound link map.
2. **Broken wikilinks:** Find links pointing to non-existent pages.
3. **Index completeness:** Every wiki page should appear in `index.md`.
4. **Frontmatter validation:** All required fields present, tags in taxonomy.
5. **Stale content:** Pages with `updated` >90 days older than newest source.
6. **Contradictions:** Pages with conflicting claims. Surface all `contested: true` pages.
7. **Quality signals:** List `confidence: low` pages.
8. **Source drift:** Check `sha256:` in raw/ files for mismatches.
9. **Page size:** Flag pages over 200 lines.
10. **Tag audit:** List all tags in use, flag any not in the taxonomy.
11. **Log rotation:** If log.md exceeds 500 entries, rotate it.
12. **Report findings** with specific file paths, grouped by severity.

## Working with the Wiki

### Searching

```bash
# Find pages by content
grep -rl "transformer" "$WIKI_PATH" --include="*.md"

# Find pages by tag
grep -rl "tags:.*alignment" "$WIKI_PATH" --include="*.md"

# Recent activity
tail -20 "$WIKI_PATH/log.md"
```

### Bulk Ingest

When ingesting multiple sources at once, batch the updates:
1. Read all sources first
2. Identify all entities and concepts across all sources
3. Check existing pages for all of them (one search pass, not N)
4. Create/update pages in one pass
5. Update index.md once at the end
6. Write a single log entry covering the batch

### Obsidian Integration

The wiki directory works as an Obsidian vault out of the box:
- `[[wikilinks]]` render as clickable links
- Graph View visualizes the knowledge network
- YAML frontmatter powers Dataview queries
- The `raw/assets/` folder holds images

## Pitfalls

- **Never modify files in `raw/`** — sources are immutable.
- **Always orient first** — read SCHEMA + index + recent log before any operation.
- **Always update index.md and log.md** — these are the navigational backbone.
- **Don't create pages for passing mentions** — follow the Page Thresholds.
- **Don't create pages without cross-references** — every page must link to 2+ others.
- **Frontmatter is required** on every wiki page.
- **Tags must come from the taxonomy** — add new tags to SCHEMA.md first.
- **Keep pages scannable** — split pages over 200 lines.
- **Handle contradictions explicitly** — don't silently overwrite.
