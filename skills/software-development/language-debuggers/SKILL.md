---
name: language-debuggers
description: "Debug running programs interactively: Python (pdb, debugpy) and Node.js (node inspect, CDP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, breakpoints, dap, cdp]
---

# Language Debuggers

Attach interactive debuggers to Python and Node.js processes without restart.

---

## Python (pdb + debugpy)

Three tools, picked by situation:

| Tool | When |
|---|---|
| `breakpoint()` + pdb | Local, interactive, simplest. Add `breakpoint()` in source, run normally, get a REPL. |
| `python -m pdb` | Launch an existing script under pdb with no source edits. |
| `debugpy` | Remote / headless / attach to already-running process. Talks DAP, works for long-lived processes (gateway, daemon, PTY children). |

**Start with `breakpoint()`.** It's the cheapest thing that works.

### Local debugging
```python
def some_function():
    breakpoint()  # Drops into pdb REPL here
    x = compute()
    return x
```

### Remote / headless (debugpy)
```bash
# Install
pip install debugpy

# Start a server in the target process
python -m debugpy --listen 5678 --wait-for-client script.py

# Attach from another terminal
python -m debugpy --connect localhost:5678
```

### Post-mortem
```python
import pdb, sys
pdb.post_mortem(sys.exc_info()[2])
```

---

## Node.js (node inspect + CDP)

Two tools:

| Tool | When |
|---|---|
| `node inspect` | Built-in, zero install, CLI REPL. Best for quick poking. |
| `chrome-remote-interface` | Scriptable from Node/Python; automate many breakpoints, collect state across runs, or debug non-interactively from an agent loop. |

**Prefer `node inspect` first.** It's always available.

### Quick poking
```bash
node inspect script.js          # Launch under debugger
node inspect -p <pid>           # Attach to running process
```

Inside the REPL:
- `cont` / `c` — continue
- `next` / `n` — step over
- `step` / `s` — step in
- `out` / `o` — step out
- `repl` — evaluate expressions in the current frame
- `sb('file.js', 42)` — set breakpoint at line 42

### CDP / scriptable
```bash
npm install chrome-remote-interface
node -e "const CDP = require('chrome-remote-interface'); CDP((client) => { ... })"
```

---

## When to Use

- A test fails and the traceback doesn't reveal why a value is wrong.
- You need to step through a function and watch a collection mutate.
- A long-running process (gateway, TUI, daemon) misbehaves and you can't restart it.
- Post-mortem: inspect locals at a crash site.
- A subprocess / child (Python `_SlashWorker`, PTY bridge worker) is the actual bug site.

**Don't use for:** things `print()` / `logging.debug` solve in under a minute.
