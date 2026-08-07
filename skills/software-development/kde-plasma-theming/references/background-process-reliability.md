# Background Process Reliability for Long-Running Downloads

Observations from a sustained 11-hour bulk download of 3,751 themes from the KDE Store via the OCS API.

## The Problem: Background Processes Die Silently (SIGTERM 143)

When running Python downloaders in background mode via `terminal(background=true, notify_on_complete=true)`:

| Symptom | Exit Code | Timing |
|---------|-----------|--------|
| Process killed during first page | 143 (SIGTERM) | ~8 minutes after launch |
| Process killed mid-category | 143 (SIGTERM) | ~8 minutes after launch |
| Process killed while log shows progress | 143 (SIGTERM) | ~8 minutes after launch |
| Forground max timeout | N/A | 600s hard limit |

**Root cause:** `notify_on_complete=true` adds a notification-delivery lifecycle that reaps the child process after ~8 minutes, regardless of the configured `timeout` value. This manifests as exit code 143 (SIGTERM). The reaping is tied to the notification delivery mechanism, not a general shell or system session timeout. Verified: process with `notify_on_complete=true` died at ~460s-850s across 4 separate runs; process WITHOUT it survived 33+ minutes on the same system, same script, same working directory.

## Solution: Omit notify_on_complete=true

Background processes launched **WITHOUT** `notify_on_complete=true` survive indefinitely — tested at 33+ minutes with no signs of termination. The process IS still killable via `process(action='kill')`, still produces stdout/stderr readable with `process(action='log')`, and still responds to polling.

### How to run reliably

```bash
# No notify_on_complete — survives indefinitely
terminal(background=true, command="python3 -u script.py > logfile 2>&1", timeout=14400)

# Monitor with polling
process(action='poll', session_id='proc_xxx')
# Check log file for output: cat logfile
```

### Trade-off

| Approach | Pros | Cons |
|----------|------|------|
| `notify_on_complete=true` | You get a notification when done | Process killed at ~8 min |
| No notification | Process survives indefinitely | You must poll manually |

For long downloads (10+ hours), omit `notify_on_complete=true` and poll periodically. For short tasks (minutes), use `notify_on_complete=true` and accept the ~8-min limit.

### Log staleness mitigation

Even without `notify_on_complete=true`, shell `>` redirect can buffer log output because the pipe buffer (4KB default) fills before the OS flushes. Mitigation:

```bash
# stdbuf -oL forces line-buffered output through the pipe
stdbuf -oL python3 -u script.py > logfile 2>&1

# Alternative: write to a file directly from Python
# sys.stdout = open("logfile", "w", buffering=1)
If polling reports `running` but the log is stale, the issue is pipe buffering, not a dead process.

## Resumability Design

The download script checks `if dpath.exists() and size >= 500 bytes` before downloading, so partial progress is always safe to resume from. Clean up error XML artifacts first:

```bash
find <archive-dir> -size -500c -type f -delete
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Max reliable lifetime WITH notify_on_complete | ~8 minutes |
| Max reliable lifetime WITHOUT notify_on_complete | 33+ minutes (tested) |
| Category 722 runtime (107 new + 85 existing, 10s gap) | ~33 minutes |
| Category 722 total size | 136 MB |
| Items without download links | ~0.5% of total |
| Log staleness with shell redirect + `-u` | Up to several minutes |

## Resumability Design

The download script checks `if dpath.exists() and size >= 500 bytes` before downloading, so partial progress is always safe to resume from. Clean up error XML artifacts first:

```bash
find <archive-dir> -size -500c -type f -delete
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Max reliable background process lifetime | ~8 minutes (platform limit) |
| Max foreground timeout | 600s |
| Per-category chunk time (10s gap) | 30 min – 2 h (cats 717–114) |
| Color Schemes (cat=112) chunk time | ~5.7 h (split across multiple runs) |
| Items processed per burst | ~20 per 200s (before any potential limit) |
| Log staleness with shell redirect + `-u` | Up to several minutes |
