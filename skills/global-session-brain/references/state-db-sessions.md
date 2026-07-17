# Querying Hermes State DB for Session Data

The canonical session store is `~/.hermes/state.db` — a SQLite database. Session JSON files in `~/.hermes/sessions/` are a secondary representation and may be absent or stale for recent sessions.

## Schema

### `sessions` table — one row per conversation

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,           -- e.g. '20260611_190438_422897'
    source TEXT NOT NULL,          -- 'tui' (terminal UI), 'cron', etc.
    user_id TEXT,
    model TEXT,                    -- e.g. 'deepseek-v4-flash'
    model_config TEXT,             -- JSON blob with config
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,      -- Unix timestamp
    ended_at REAL,                 -- Unix timestamp (NULL if still active)
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    title TEXT,                    -- Auto-generated title
    cwd TEXT,                      -- Working directory
    archived INTEGER NOT NULL DEFAULT 0
);
```

### `messages` table — individual turns

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,         -- FK → sessions.id
    role TEXT NOT NULL,               -- 'user', 'assistant', 'tool'
    content TEXT,                     -- Full message text (nullable)
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,          -- Unix timestamp (NOT created_at)
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,
    reasoning_details TEXT,
    ...                              -- additional columns exist
);
```

## Finding Unprocessed Sessions

Filter out `source='cron'` — those are brain extraction runs themselves, not knowledge sources.

```sql
-- Recent non-cron sessions, newest first
SELECT id, source, started_at, ended_at, title, message_count 
FROM sessions 
WHERE source != 'cron' 
  AND archived = 0
  AND id NOT IN (<already_processed_ids>)
ORDER BY started_at DESC;

-- Sessions with activity in the last N hours
-- IMPORTANT: Join messages table — filtering by sessions.started_at alone
-- silently misses ongoing sessions (started days ago but with recent messages).
SELECT DISTINCT s.id, s.title, s.started_at, s.ended_at,
       s.message_count, COUNT(m.id) as recent_msgs
FROM sessions s
JOIN messages m ON m.session_id = s.id
WHERE s.source != 'cron'
  AND s.archived = 0
  AND m.timestamp > (strftime('%s','now') - 7200)  -- last 2 hours
  AND m.role IN ('user', 'assistant')
  AND s.id NOT IN (<already_processed_ids>)
GROUP BY s.id
ORDER BY recent_msgs DESC;
```

## Reading Session Messages

Once you have a session ID, fetch its messages:

```sql
-- Full conversation for a session
SELECT id, role, content, timestamp 
FROM messages 
WHERE session_id = '<session_id>' 
ORDER BY timestamp ASC;
```

The `content` column contains the full message text. Role values:
- `user` — User's question/statement
- `assistant` — AI's response (contains the reasoning and answers)
- `tool` — Tool call results (JSON blobs, file contents, etc. — can be large, focus on error outputs and factual returns)

**Important:** Many `assistant` and `tool` role messages have NULL or empty `content` — these are internal bookkeeping rows (tool-call cycles, intermediate step records, etc.) with zero semantic value. When reading messages for brain extraction, always filter them out:
```sql
SELECT id, role, content, timestamp
FROM messages
WHERE session_id = '<session_id>'
  AND content IS NOT NULL AND content != ''
ORDER BY timestamp ASC;
```
Without this filter, you may get 50+ empty rows between every meaningful exchange, making extraction slow and noisy.

## Tracking Processed Sessions

The brain manifest at `~/.hermes/brain/.brain_manifest.json` tracks which session IDs have been processed. Update it after extraction:

```python
manifest["processed"][session_id] = "2026-06-12T17:00:00+00:00"
```

There is no "export to JSON" step needed — read directly from state.db and write extracted knowledge to wiki/.md files.

## Common Query Patterns

```bash
# Count total sessions by source
sqlite3 ~/.hermes/state.db "SELECT source, COUNT(*) as cnt FROM sessions GROUP BY source ORDER BY cnt DESC;"

# Sessions with message counts
sqlite3 ~/.hermes/state.db "SELECT id, datetime(started_at, 'unixepoch'), message_count, title FROM sessions WHERE source != 'cron' ORDER BY started_at DESC LIMIT 10;"

# Sessions with no messages (empty/crashed) — skip these
sqlite3 ~/.hermes/state.db "SELECT id FROM sessions WHERE message_count = 0;"
```

## Note: `~/.hermes/sessions/sessions.db`

This file exists but is typically **empty** (0 bytes). It is NOT the canonical session store. All real session data is in `~/.hermes/state.db`.

## Note: Request dump files

Files named `request_dump_*.json` in `~/.hermes/sessions/` are API error/crash dumps (e.g., `max_retries_exhausted`), not conversation sessions. Ignore them during extraction.
