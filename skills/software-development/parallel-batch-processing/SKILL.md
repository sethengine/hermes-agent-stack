---
name: parallel-batch-processing
description: "Fan-out/fan-in batch processing with subagents — dispatch parallel workers for independent work items, collect and aggregate results, run post-processing. For data extraction, batch file processing, migrations, and bulk operations."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [subagent, parallel, batch, aggregation, fan-out, fan-in, workflow]
    category: software-development
    related_skills: [subagent-driven-development, global-session-brain]
---

# Parallel Batch Processing with Subagents

**Dispatch independent work items across parallel subagents, collect manifests, aggregate, and post-process.**

## When to Use

Use this pattern when:
- You have **N independent work items** (sessions, files, records, datasets)
- Each item can be processed without knowing about the others
- Results need to be **collected and consolidated** (graph injection, database updates, merged files)
- Parallel execution would save wall-clock time

**vs. sequential processing:** Cheaper per-item (no context pollution), faster wall-clock (parallel), but needs aggregation logic.

**vs. subagent-driven-development:** SDD is sequential code with 2-stage review per task. This is parallel execution of identical task types with result aggregation.

## The Pattern

```
┌──────────────┐
│  Work Items  │  N items, each independently processable
└──────┬───────┘
       │
       ▼
 ┌──────────────┐
 │  Partition   │  Split into M batches (M ≤ 3, tool limit)
 │  into Batches │
 └──────┬───────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
 ┌──────────┐    ┌──────────┐    ┌──────────┐
 │Subagent 1│    │Subagent 2│    │Subagent 3│  Each processes its batch
 │Items A-D │    │Items E-H │    │Items I-L │  independently
 └─────┬────┘    └─────┬────┘    └─────┬────┘
       │               │               │
       ▼               ▼               ▼
   File manifest   File manifest   File manifest   Each returns list of
   (files.json)    (files.json)    (files.json)    created/modified files
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
                ┌──────────────┐
                │  Aggregate   │  Combine manifests, verify files exist
                │  Manifests   │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ Post-Process  │  Inject into graph, update indices,
                │               │  validate, clean up temp files
                └──────────────┘
```

## Step-by-Step

### Step 1: Identify Work Items

Query the source of truth to find what needs processing:

```bash
python3 -c "
import sqlite3, json
# Find unprocessed items
items = db.execute('SELECT id, message_count, title FROM items ORDER BY priority LIMIT 50')
"
```

Prioritize by value: larger items with more durable content first. Cap at 8-12 per run.

### Step 2: Partition into Batches

Split items across subagents, keeping them balanced:

```python
batches = [items[i:i+2] for i in range(0, len(items), 2)]
# Max 3 batches (parallel subagent limit), 2-4 items per batch typical
```

### Step 3: Dispatch Subagents (Parallel)

Use `delegate_task` with identical task structure per batch.

**⚠️ Parameter naming:** The `delegate_task` tool uses `goal` (task objective) and `context` (background info) — NOT `description` or `prompt`. Using `description`/`prompt` produces a validation error with no further guidance:

> `Provide either 'goal' (single task) or 'tasks' (batch).`

The `description` parameter is a separate optional UI tracking label (3-5 words, shown in the session UI), not the task prompt. Always use `goal` for the task.

**⚠️ Synchronous execution in cron/one-shot mode:** The `background=true` flag is **silently ignored** in cron jobs, `hermes -z` one-shot runners, Kanban workers, and stateless HTTP endpoints. From the tool:

> `background=true is not available in this session — it cannot receive a detached subagent result after the turn ends (a one-shot runner such as hermes -z, a cron job, a Kanban worker, or a stateless HTTP endpoint). The subagent(s) ran SYNCHRONOUSLY.`

All subagents run **sequentially** in these contexts — no parallelism. Total wall-clock time is the sum of every subagent's runtime (observed: 34s + 67s + 31s = ~132s for 3). Plan timeouts and batch size accordingly. The pre-run lock still protects against overlapping cron jobs; only intra-run concurrency is lost.

```python
subagents = []
for batch in batches:
    subagents.append(delegate_task(
        goal="Process batch: extract knowledge from N sessions",
        context=f""""
        ITEMS TO PROCESS:
        {json.dumps(batch, indent=2)}

        RULES:
        - For each item: read content from source, extract durable knowledge
        - Write output files to the correct subdirectory
        - Each file needs YAML frontmatter with source session, date, category
        - Max 200 words per file
        - Include [[wiki-links]] to related concepts

        RETURN FORMAT:
        Return a JSON object with an 'all_files' key containing a list of
        absolute paths to every file you created.
        """,
        subagent_type="leaf"
    ))
```

### Step 4: Collect Manifests

Each subagent returns a JSON manifest of created files. Aggregate:

```python
all_new_files = []
for result in subagent_results:
    summary = json.loads(result['summary'])
    all_new_files.extend(summary['all_files'])
```

### Step 5: Verify Files Exist

```python
for f in all_new_files:
    if not os.path.exists(f):
        log.warning(f'Subagent claimed {f} but file not found — skipping')
```

### Step 6: Post-Processing

Build the aggregated result and perform post-processing:

```python
# Example: Build graph injection nodes
for f in all_new_files:
    node_id = make_node_id(f)
    nodes.append({'id': node_id, 'file_type': 'document', ...})
    for related in find_related(node_id):
        links.append({'source': node_id, 'target': related, 'relation': 'references', ...})

# Then inject, verify, clean up
```

### Step 7: Clean Up

Remove temp files, release locks, record completion:

```bash
rm -f /tmp/new_nodes_*.json /tmp/new_links_*.json
```

## Subagent Prompt Template

For the most reliable results, structure every subagent prompt with these sections:

```
GOAL: [Single sentence — what to produce]

ITEMS TO PROCESS:
[Array of items with IDs, sources, metadata]

RULES:
• [How to read source data]
• [How to write output files — include exact directory paths]
• [File naming conventions]
• [Maximum file size/content limits]
• [Format requirements — YAML frontmatter, metadata, etc.]

RETURN FORMAT:
[JSON schema or plain-text description of what to return]
```

## Output Manifest Convention

Every subagent should return its created files in a consistent format:

```json
{
  "all_files": [
    "/absolute/path/to/file1.md",
    "/absolute/path/to/file2.md"
  ]
}
```

Use absolute paths, not relative or `~/` prefixed ones, so the parent agent can verify existence without path resolution.

## Pre-Run Lock (Prevent Concurrent Runs)

For cron workloads, acquire a lock before starting and release after completion:

```bash
LOCK="/path/to/.batch-lock"
if [ -f "$LOCK" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || echo 0)))
    if [ "$LOCK_AGE" -gt 3600 ]; then
        # Stale lock — check if actually running
        if ! ps aux | grep -E "batch|subagent" | grep -qv grep; then
            python3 -c "open('$LOCK','w').write(str(int(__import__('time').time())))"
        else
            exit 0
        fi
    else
        exit 0
    fi
else
    python3 -c "open('$LOCK','w').write(str(int(__import__('time').time())))"
fi
```

## Unique Temp File Names

When subagents write shared temp files, use timestamped names to avoid sibling collisions:

```python
ts = int(time.time())
with open(f'/tmp/new_nodes_{ts}.json', 'w') as f:
    json.dump(nodes, f)
with open(f'/tmp/new_links_{ts}.json', 'w') as f:
    json.dump(links, f)
```

## Subagent Deviation and Batch Failure Verification

**Problem 1 — subagents process items outside their assigned batch.** Parallel subagents with disjoint item assignments may deviate and process an item from another batch (observed 2026-08-01: Batch B processed a Batch C session). Result: one item double-processed, another never processed, misleading "N files created" self-reports.

**Problem 2 — a transient failure can zero out an entire batch.** One batch hit an HTTP 503 mid-run and produced nothing; its items were only saved because a deviating sibling happened to cover one of them. Do not assume a batch's items are done because the subagent "completed" — errors can abort silently while the summary still looks plausible.

**Prevention:**
- State the exact allowed item IDs in every subagent prompt: "Process ONLY these items: <ids>. Do not touch any other item."
- Keep assignments disjoint, but design the post-run reconciliation (below) as the source of truth rather than relying on subagents to respect boundaries.

**Mandatory post-run verification — reconcile self-reports against ground truth:**
1. For every assigned item, confirm it is actually recorded as done in the tracking store (manifest/DB), not merely claimed by a subagent.
2. For every batch that errored or returned 0 outputs, retry it with the SAME assignment — but first check the tracking store, since a deviating sibling may have already covered some items.
3. Build downstream post-processing (graph injection, index updates) ONLY from outputs verified to exist on disk AND items confirmed done in the tracking store — never from subagent summaries alone.

**Idempotency check on inputs (meta-items):** Before dispatching, check whether each work item's output ALREADY exists. In backlog-processing pipelines, some items are prior runs of the same pipeline (e.g., a session whose transcript is an earlier extraction subagent and whose wiki files already exist). Processing them creates duplicates and wasted tokens. If an item's described outputs are already on disk, mark it done without re-processing — read the item's first user message to spot these meta-items cheaply.

## Verification Loop

After post-processing, run a verification before declaring success:

1. **Count check**: Expected N outputs, got N? If mismatch, diagnose.
2. **Content check**: Sample 1-2 outputs — do they look right?
3. **Link/edge check**: If injecting into a graph, verify that injected links have correct direction (post-processing tools may reverse them).
4. **Cleanup**: Remove temp files, release locks, update tracking records.

## Related

- **subagent-driven-development** — Sequential implementation with 2-stage review (complementary pattern)
- **global-session-brain** — Uses this pattern for batch knowledge extraction from sessions
