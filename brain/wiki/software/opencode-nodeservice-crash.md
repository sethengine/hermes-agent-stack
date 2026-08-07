---
source: "20260712_222319_475878"
date: "2026-07-12"
category: "software"
tags: [opencode, crash, nodeservice, electron, v8, sigabrt]
---

# OpenCode NodeService Crash (SIGABRT)

## The Crash

`ai.opencode.desktop` utility process (`node.mojom.NodeService` — Electron's embedded Node.js) crashes with **SIGABRT (Signal 6)**. Single-frame coredump — typical of a crash inside **V8 JIT-compiled code** (no C++ unwind frames).

## Key Facts

| Field | Value |
|-------|-------|
| OpenCode version | 1.17.18 |
| Binary modified | 7 min before crash |
| Process type | `utility` → `node.mojom.NodeService` |
| Crash type | SIGABRT (abort/assertion failure) |
| Core dump | 30MB (consistent with V8 heap snapshot) |

## Root Cause (Likely)

1. **V8 OOM abort** — NodeService handles OpenAI/local model API calls; large response can exhaust heap
2. **Internal V8 assertion** — `DCHECK` failure after an Electron update
3. **Recurrent**: Every session's `utility.log` shows `sidecar exited { code: 0 }` at end

## Diagnosis Commands

```bash
# Launch with visible stderr
/opt/OpenCode/ai.opencode.desktop --no-sandbox 2>&1 | tee /tmp/opencode.log

# Check OOM events
dmesg | grep -i 'oom\|kill.*opencode' | tail -5

# Check journal around crash
journalctl -u user@1000.service --since "23:00" --until "23:03" --no-pager | grep -i 'opencode\|abort\|fatal'
```

## Related

- Binary was auto-updated minutes before the crash
- OpenCode auto-restarts successfully after the crash
- [[crash-analysis-methodology]] for general crash investigation approach
