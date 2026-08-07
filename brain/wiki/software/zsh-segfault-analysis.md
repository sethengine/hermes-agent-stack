---
source: "20260712_222319_475878"
date: "2026-07-12"
category: "software"
tags: [zsh, crash, segfault, signal-handling, powerlevel10k, gitstatus]
---

# zsh 5.9 Recursive Signal Handler Use-After-Free Crash

## The Bug

zsh 5.9 contains a known use-after-free in the job table during **recursive SIGCHLD handling on exit**. Triggered on Manjaro with [[powerlevel10k]] and [[gitstatus]] installed.

## Crash Flow (3-layer recursion)

- **Layer 1**: ZLE widget (prompt refresh) runs `$(...)` command substitution → `waitjobs` → `sigsuspend`
- **Layer 2**: SIGCHLD arrives → `zhandler` → `zexit()` runs zshexit hooks (`_p9k_worker_cleanup`, `_p9k_instant_prompt_cleanup`, `_gitstatus_cleanup_*`) → those also do command substitution → `waitjobs` → `sigsuspend`
- **Layer 3**: Another SIGCHLD during zexit → recursive `zhandler` → `deletejob` on already-corrupted job table → **SEGV (Signal 11)**

Stack trace signature: `deletejob → printjob → wait_for_processes → zhandler → ... → callhookfunc → zexit → zhandler → sigsuspend → waitjobs`

## Fix

Upgrade to **zsh 5.9.1-1** or later (in Manjaro repos). Key patches:

| Commit | Fix |
|--------|-----|
| `5d2bea4a` (54479) | Fix use-after-free when handling TRAPEXIT |
| `49de4e14` (45837) | Fix process group restoration on exit |
| `54540` | Avoid clobbering `sig` in signal handlers |
| `04a9b828` (53005) | Fix off-by-one resetting signals on subshell entry |
| `816ec7f3` (54525) | Fix signal handling during FIFO redirects |

**Upgrade**: `sudo pacman -Syu zsh`

## Trigger Conditions

- zsh 5.9 (`5.9-6` on Manjaro)
- [[powerlevel10k]] with instant prompt and worker threads enabled
- [[gitstatus]] daemon cleanup hooks
- Happens on terminal close or shell exit during prompt rendering
