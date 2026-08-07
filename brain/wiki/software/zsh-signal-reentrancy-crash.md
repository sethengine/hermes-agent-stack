---
source: "20260716_221852_bb0332"
date: "2026-07-16"
category: "software"
tags: [zsh, crash, sigsegv, signal-reentrancy, powerlevel10k, manjaro]
wiki-links: [zsh_performance_tuning, zsh_p10k_exit_sigchld_workaround]
---

# Zsh Signal Reentrancy Crash (5.9-6)

zsh 5.9-6 on Manjaro has a **signal re-entrancy bug** during exit processing. The crash signal varies — observed as **SEGV** (Signal 11, null dereference) or **ABRT** (Signal 6, abort during history save), depending on which internal path is torn down during re-entry.

**Crash path:** Terminal close (SIGHUP) → `zhandler` → `zexit()` → `callhookfunc()` → p10k `_p9k_worker_cleanup` kills worker → SIGCHLD → `zhandler` re-entered → job state partially torn down → null dereference → **SEGV**.

Key factor: `zhandler` is entered **twice** — the exit-triggering signal enters it the first time, then the p10k worker cleanup generates SIGCHLD which re-enters it while job state is being torn down.

**SIGABRT variant crash path:** Terminal close (SIGHUP) → `waitjobs()` → `sigsuspend()` → [SIGHUP] → `zhandler` → `zexit()` → crash during **history save** (abort, not null dereference). Same root cause (signal re-entrancy), different internal sub-path within zexit().

**Fix:** Upgrade to zsh 5.9.1-1 in Manjaro repos:
```sh
pacman -Syu zsh
```
