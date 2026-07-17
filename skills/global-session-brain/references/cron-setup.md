# Cron Job Setup — Global Session Brain

The brain uses a **Hermes-native cron job** for periodic extraction.

## Schedule

**Every 2 hours** — processes sessions that completed since the last run.

```
schedule: 0 */2 * * *
skill: global-session-brain
prompt: /brain extract --since 2h
```

## What it does each run

1. Query `~/.hermes/state.db` SQLite database for sessions with activity in the time window that are not yet in the manifest. See the `/brain extract` section in the main skill for the exact SQL query. (The old `track_sessions.py` script only finds JSON files which may be absent for recent sessions — always check state.db first.)
2. For each new session: read session content from the `messages` table in state.db, extract durable knowledge
3. Categorizes and writes to `~/.hermes/brain/wiki/{category}/{file}.md`
4. Update `.brain_manifest.json` via `terminal("python3 -c '...'")` — `execute_code` is blocked in cron mode. Add new session IDs, update `last_extraction`, and set `total_extracted_files` to the count of wiki `.md` files (use `glob.glob()`).
5. Build a `new_nodes.json` file, inject new document nodes into `graph.json` via `scripts/inject-graph-nodes.py`, and run `graphify cluster-only ~/.hermes/brain` to re-cluster. (The `graphify update` command only processes code files, not markdown documents. See the main skill for alternative approaches.)

## Token cost per run

| Component | Tokens |
|-----------|--------|
| Session listing (script) | ~0 (deterministic) |
| Reading session JSONs (3-5 new sessions) | ~15-25K |
| Extraction reasoning | ~5-10K |
| Writing wiki files | ~2-5K |
| Graph node injection + cluster-only | ~0 (deterministic) |
| **Typical total per run** | **~25-40K tokens** |

If no new sessions exist since last run: ~100 tokens (just the session listing).

## How to install the cron job

Use the Hermes cron tool:

```bash
hermes cron create --schedule "0 */2 * * *" --skill global-session-brain "/brain extract --since 2h"
```

## How to check status

```bash
hermes cron list
```

## Manual extraction

To run extraction immediately on a specific session:

```
/brain extract --session session_20260611_190438_422897
```

To run on all unprocessed sessions now:

```
/brain extract
```

## First run (initialization)

For the first run, process all existing sessions:

```
/brain extract
```

This will process ~20 sessions (5.7 MB, 890 messages) and populate the wiki. Expect ~100-200K tokens for the initial extraction.
