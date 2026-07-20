# Userspace Process Crash Analysis — Coredump Investigation

A systematic methodology for analyzing individual process crashes logged by `coredumpctl` and systemd-journald. Complements the kernel/system-level focus of `system-log-deep-dive.md`.

## Quick Reference — Crash Types

| Signal | Name | Meaning | Typical Cause |
|--------|------|---------|---------------|
| 6 | SIGABRT | Process aborted itself | Assertion failure, OOM abort, `process.abort()`, V8 fatal error |
| 11 | SEGV | Segmentation fault | Use-after-free, NULL deref, buffer overflow, corrupted pointer |

## Investigation Pipeline

### 1. Capture the Crash

```bash
# Recent crashes
coredumpctl list | tail -20

# Details + stack trace
coredumpctl info <PID>

# Stack trace only
coredumpctl info <PID> 2>/dev/null | sed -n '/Stack trace/,/^$/p'
```

If `coredumpctl info` shows only a truncated stack trace, you may need the debug symbols package:

```bash
# Find the debug package
pacman -Qs <binary-name>-debug
pkgfile <binary-name>-debug

# Install it
sudo pacman -S <binary-name>-debug
coredumpctl info <PID>  # now shows line numbers
```

### 2. Read the Stack Trace

**Full stack trace pattern:**

```
#0  0x00007f... function_name (/usr/lib/... + 0x1234)
#1  0x00007f... deletejob (/usr/bin/zsh + 0x62c5e)
#2  0x00007f... printjob (/usr/bin/zsh + 0x64caa)
...
```

Read the trace from **top to bottom** (shallowest to deepest):
- **#0**: The exact instruction that crashed — start here
- **#1**: The caller that triggered #0
- Use known function names (e.g., `deletejob`, `malloc`, `free`, `abort`) to infer what happened
- Offsets like `+ 0x62c5e` aren't useful without debug symbols

**Crash classification by stack pattern:**

| Pattern | Likely Cause |
|---------|-------------|
| `deletejob` / `freejob` / job table corruption | Use-after-free in job management (zsh signal handling) |
| `malloc` / `free` / `realloc` with invalid pointer | Heap corruption, use-after-free in memory allocator |
| `abort()` / `__assert_fail` | Explicit assertion failure — check for the assertion message |
| Single frame only (`#0  0x... n/a (n/a + 0x0)`) | V8 JIT code crash — the abort happened in JIT-compiled JavaScript, not in C++ |
| `jscregexp` / `v8::` / `node::` | V8 or Node.js internal crash |
| `std::terminate` / `__cxa_throw` | C++ unhandled exception |

### 3. Identify the Process Type

From `coredumpctl info`, look at `Command Line:`:

| Process Description | What it Is | Where to Find App Logs |
|--------------------|------------|----------------------|
| `/usr/bin/zsh -l` | Interactive shell | No app log; check `.zshrc`, hooks, zshexit |
| `--utility-sub-type=node.mojom.NodeService` | Electron Node.js utility process | Check `~/.config/<app>/logs/utility.log`, `server.log` |
| `--type=renderer` | Electron/Chrome renderer | Check `~/.config/<app>/logs/renderer.log` |
| `--type=gpu-process` | GPU process | Check `~/.config/<app>/logs/gpu.log` |

### 4. Correlate with Application Logs

Find the app's log directory (varies by app):

```bash
# Common Electron app config paths
ls ~/.config/<app-name>/logs/   # OpenCode, VS Code, Discord
ls ~/.config/<app-name>/crashpad/  # Crashpad minidumps (Standard)
```

Check for a `crash.log` that confirms the crash reporter was running:

```
[2026-07-12 23:02:51.814] [info]  (crash) crash reporter started { path: '.../Crashpad' }
```

Check the relevant process log (`utility.log` for NodeService, `renderer.log` for renderer crashes, etc.) at the same timestamp:

```
[2026-07-12 23:02:46.951] [warn]  (utility) sidecar exited { code: 0 }
```

### 5. Find the Fix

| Crash Pattern | Fix |
|---------------|-----|
| Shell crash in job table / signal handling | Upgrade the shell — zsh 5.9.1 fixes use-after-free in TRAPEXIT handling |
| Electron utility process SIGABRT (single frame) | Check for V8 OOM — relaunch from terminal to see stderr |
| Electron renderer crash | Check GPU drivers, disable hardware acceleration as test |
| Recurring crash in every session | File a bug report with the app vendor — include coredumpctl output |

### 6. Capture V8/Node.js Diagnostic Output

When a Node.js utility process crashes, `coredumpctl info` often shows only 1 frame. To get the actual error:

```bash
# Launch the app from terminal and watch stderr
<app-binary> 2>&1 | tee /tmp/app.log

# When the crash happens, V8 typically prints to stderr:
#   FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
#   FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed - process out of memory
#   #
#   # Fatal error in , line 0
#   # --- raw stack ---
```

## Common Case Studies

### Case 1: zsh SIGSEGV — Signal Re-Entrancy During Exit

This is a **re-entrancy crash** in zsh: a signal handler fires while the shell is already processing exit, and the handler tries to manage jobs whose state is partially torn down.

#### Crash Pattern (Two zhandler Invocations)

```
Stack trace of thread 122087:
#0  0x... n/a (/usr/bin/zsh + 0x5e463)          ← SEGV site (use-after-free in job table)
#1  0x... deletejob (/usr/bin/zsh + 0x62c5e)     ← deleting a job
#2  0x... printjob (/usr/bin/zsh + 0x64caa)      ← printing job status
#3  0x... n/a (/usr/bin/zsh + 0x65e27)
#4  0x... wait_for_processes (/usr/bin/zsh + 0xa790d)  ← managing child processes
#5  0x... zhandler (/usr/bin/zsh + 0xa1595)      ← SECOND zhandler (SIGCHLD handler)
#6  0x... doshfunc (/usr/bin/zsh + 0x40ffc)      ← running shell function via hook
#7  0x... callhookfunc (/usr/bin/zsh + 0xbdd24)  ← calling zshexit hook
#8  0x... zexit (/usr/bin/zsh + 0x28fd5)         ← exit path
#9  0x... zhandler (/usr/bin/zsh + 0xa17c1)      ← FIRST zhandler (SIGHUP/SIGTERM)
#10 0x... n/a (libc.so.6 + 0x3e8f0)              ← signal trampoline
#11 0x... n/a (libc.so.6 + 0x94ade)
#12 0x... n/a (libc.so.6 + 0x94b04)
#13 0x... __sigsuspend (libc.so.6 + 0x3eb85)     ← zsh was waiting for child
#14 0x... n/a (/usr/bin/zsh + 0x66eff)
#15 0x... waitjobs (/usr/bin/zsh + 0x66fdf)      ← waiting for jobs to finish
```

**Key observation — TWO zhandler invocations at different offsets:**
- `0xa17c1` (frame #9): handler for exit-triggering signals (SIGHUP, SIGTERM) — calls `zexit()`
- `0xa1595` (frame #5): SIGCHLD handler — manages job table

#### Crash Flow (Step by Step)

1. **Primary signal arrives** (SIGHUP from terminal close, or SIGTERM from system shutdown)
2. `zhandler` @0xa17c1 fires → calls `zexit()` — starts shell exit
3. `zexit()` calls `callhookfunc()` → runs `zshexit` hooks
4. **p10k's `_p9k_worker_cleanup` hook** (worker.zsh:91-96) runs → kills the worker process
5. The kill sends **SIGCHLD** → `zhandler` @0xa1595 re-enters
6. `wait_for_processes` → tries to update job state
7. `printjob` → `deletejob` → **SEGV** (job table is partially torn down during exit)

#### Root Cause

**Signal re-entrancy:** zsh 5.9's exit path runs hooks that can spawn or kill child processes, generating SIGCHLD. The SIGCHLD handler re-enters job management code (`deletejob`/`printjob`/`wait_for_processes`) while the job table is in an inconsistent state during exit teardown — use-after-free on job data structures.

#### Specific Trigger Components

| Component | File | Role |
|---|---|---|
| p10k EXIT trap | `p10k.zsh:6376` | `trap "unset -m _p9k__*; unfunction p10k" EXIT` — runs during exit |
| p10k worker cleanup | `worker.zsh:91-96` | `_p9k_worker_cleanup` — zshexit hook that kills worker process |
| p10k worker kill | `worker.zsh:105` | `kill -- -$_p9k__worker_pid` — sends signal to worker process group |
| Manjaro config | `/usr/share/zsh/manjaro-zsh-config:6` | `setopt nocheckjobs` — prevents job warnings on exit (but doesn't prevent re-entrancy) |

#### Fix: Upgrade zsh

```bash
# Check if an update is available
pacman -Qu zsh

# Upgrade
sudo pacman -Syu zsh
```

**zsh 5.9 → 5.9.1** contains fix 54479 ("Fix use-after-free when handling TRAPEXIT").

#### Workarounds (before upgrade)

**Option A — Suppress job notifications:**
Add near the top of `.zshrc` (before p10k loads):
```zsh
setopt NO_NOTIFY
```

**Option B — Block SIGCHLD during exit hooks:**
Add before the p10k source line in `.zshrc`:
```zsh
zshexit_functions+=(_block_chld_exit)
_block_chld_exit() { trap '' CHLD; }
```

#### Additional Notes

- **Decoding crash offsets** on a stripped zsh binary: `addr2line` returns `??:?` without debug symbols. The Arch debug package (`zsh-debug`) is not available as a separate package — the build itself is stripped. Dynamic symbols (`nm -D /usr/bin/zsh`) only export library-entry symbols, not internal functions.
- **`nocheckjobs` does NOT prevent this crash** — it only suppresses the warning about running jobs on exit. The crash happens in signal handling, not in the check warning.
- **This is triggered by terminal close** (closing an Alacritty/Kitty/GNOME Terminal tab or window) or by system logout, because both send SIGHUP to the shell's process group.

### Case 2: Electron NodeService SIGABRT (single-stack-frame crash)

**Signature:**
```
Signal: 6 (ABRT)
Stack trace:
  #0  0x00007f... n/a (n/a + 0x0)
  ELF object binary architecture: AMD x86-64
```

**Analysis:**
1. Only 1 frame with no library — crash is inside V8 JIT-compiled code
2. Process is `node.mojom.NodeService` — Electron's in-process Node.js runtime
3. SIGABRT means `abort()` was called explicitly (not a SEGV)
4. App log shows `sidecar exited { code: 0 }` at the same timestamp

**Most likely causes (in order):**
- V8 heap OOM (`FATAL ERROR: Reached heap limit Allocation failed`)
- V8 internal assertion failure (DCHECK)
- Native Node.js module crash (`.node` files like pty.node, msgpackr)

**Diagnosis:** Relaunch app from terminal to capture stderr where V8 writes the abort reason.

**Binary freshness check:** Check if the app binary was recently updated — a new version could have introduced a regression:
```bash
stat /opt/<app>/<binary>
# Compare with crash time
```
