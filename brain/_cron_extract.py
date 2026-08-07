#!/usr/bin/env python3
"""Cron brain extraction: Phase 1 + Phase 2 session discovery."""
import subprocess, json, os, glob, time
from datetime import datetime, timezone

HOME = os.path.expanduser('~')
BRAIN = os.path.join(HOME, '.hermes', 'brain')
MANIFEST = os.path.join(BRAIN, '.brain_manifest.json')
STATE_DB = os.path.join(HOME, '.hermes', 'state.db')
GRAPH_JSON = os.path.join(BRAIN, 'graphify-out', 'graph.json')
LOCK = os.path.join(BRAIN, '.extract-lock')

# Check/stale lock
if os.path.exists(LOCK):
    lock_age = time.time() - os.path.getmtime(LOCK)
    if lock_age > 7200:
        proc_check = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'brain.*extract' not in proc_check.stdout and 'inject-graph' not in proc_check.stdout:
            print(f"Stale lock ({lock_age:.0f}s old, no process) — claiming it")
        else:
            print(f"Extraction still in progress — skipping")
            exit(0)
    else:
        print(f"Extraction already in progress (lock: {open(LOCK).read().strip()}) — skipping")
        exit(0)

# Write lock via python3 (TIRITH-safe)
with open(LOCK, 'w') as f:
    f.write(f'cron-run-{int(time.time())}')

try:
    # Load manifest
    manifest = json.load(open(MANIFEST))
    processed = set(manifest['processed'].keys())

    NOW = int(time.time())
    SINCE = NOW - 7200
    print(f"Now: {NOW} ({datetime.fromtimestamp(NOW, tz=timezone.utc).isoformat()})")
    print(f"Window: {SINCE} ({datetime.fromtimestamp(SINCE, tz=timezone.utc).isoformat()})")

    # Get all non-cron sessions from state.db
    proc = subprocess.run(
        ['sqlite3', STATE_DB, "SELECT id, title, message_count FROM sessions WHERE source != 'cron' ORDER BY started_at DESC;"],
        capture_output=True, text=True
    )
    all_lines = [l for l in proc.stdout.strip().split('\n') if l]
    print(f"Total non-cron sessions in DB: {len(all_lines)}")

    all_sids = set()
    for line in all_lines:
        sid = line.split('|')[0].strip()
        all_sids.add(sid)

    print(f"Processed in manifest: {len(processed)}")
    print(f"Unprocessed (not in manifest): {len(all_sids - processed)}")

    # Phase 1: Unprocessed sessions with recent messages
    phase1 = []
    for line in all_lines:
        parts = line.split('|')
        sid = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else ''
        
        if sid in processed:
            continue
        
        proc2 = subprocess.run(
            ['sqlite3', STATE_DB,
             f"SELECT COUNT(*) FROM messages WHERE session_id='{sid}' AND timestamp > {SINCE} AND role IN ('user','assistant') AND content IS NOT NULL AND content != '';"],
            capture_output=True, text=True
        )
        count = int(proc2.stdout.strip() or 0)
        if count > 0:
            phase1.append((sid, title, count))

    print(f"\nPhase 1 (unprocessed with recent msgs): {len(phase1)}")
    for sid, title, c in phase1:
        print(f"  {sid} | {title[:60]} | recent_msgs={c}")

    # Phase 2: Processed sessions with new messages
    processed_list = list(processed)
    phase2 = []
    
    # Process in batches of 50 to avoid excessively long queries
    for i in range(0, len(processed_list), 50):
        batch = processed_list[i:i+50]
        ids_str = ','.join(f"'{sid}'" for sid in batch)
        proc3 = subprocess.run(
            ['sqlite3', STATE_DB,
             f"SELECT s.id, s.title, COUNT(m.id) as recent_msgs FROM sessions s JOIN messages m ON m.session_id = s.id WHERE s.source != 'cron' AND m.timestamp > {SINCE} AND m.role IN ('user','assistant') AND m.content IS NOT NULL AND m.content != '' AND s.id IN ({ids_str}) GROUP BY s.id ORDER BY recent_msgs DESC;"],
            capture_output=True, text=True
        )
        for line in proc3.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('|')
            phase2.append((parts[0], parts[1], int(parts[2])))

    print(f"\nPhase 2 (processed with new msgs): {len(phase2)}")
    for sid, title, c in phase2:
        print(f"  {sid} | {title[:60]} | recent_msgs={c}")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Phase 1 candidate sessions: {len(phase1)}")
    print(f"Phase 2 candidate sessions: {len(phase2)}")
    
    # Check graph state
    if os.path.exists(GRAPH_JSON):
        d = json.load(open(GRAPH_JSON))
        print(f"Current graph: {len(d['nodes'])} nodes, {len(d['links'])} links")
    else:
        print("Current graph: NOT FOUND")

finally:
    # Release lock
    if os.path.exists(LOCK):
        os.remove(LOCK)
