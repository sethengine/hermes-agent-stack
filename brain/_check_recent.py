#!/usr/bin/env python3
"""Check most recent sessions' last message timestamps."""
import subprocess, datetime, time

NOW = int(time.time())
SINCE = NOW - 7200

proc = subprocess.run(
    ['sqlite3', '/home/sethengine/.hermes/state.db',
     "SELECT id, title, started_at, message_count FROM sessions WHERE source != 'cron' ORDER BY started_at DESC LIMIT 10;"],
    capture_output=True, text=True
)
print("Most recent sessions:")
for line in proc.stdout.strip().split('\n'):
    if not line:
        continue
    parts = line.split('|')
    sid = parts[0]
    title = parts[1] if len(parts) > 1 else ''
    
    proc2 = subprocess.run(
        ['sqlite3', '/home/sethengine/.hermes/state.db',
         f"SELECT MAX(timestamp) FROM messages WHERE session_id='{sid}' AND role IN ('user','assistant') AND content IS NOT NULL AND content != '';"],
        capture_output=True, text=True
    )
    last_ts = proc2.stdout.strip()
    
    if last_ts:
        dt = datetime.datetime.fromtimestamp(float(last_ts), tz=datetime.timezone.utc)
        in_window = float(last_ts) > SINCE
        print(f"  {sid} | {title[:50] or '(no title)'} | last_msg={dt.isoformat()} | in_2h_window={in_window}")
    else:
        print(f"  {sid} | {title[:50] or '(no title)'} | no user/assistant messages")
