---
source: "20260716_221852_bb0332"
date: "2026-07-16"
category: "software"
tags: [zsh, powerlevel10k, sigchld, workaround, exit-hooks]
wiki-links: [zsh_signal_reentrancy_crash, zsh_performance_tuning]
---

# Zsh p10k Exit SIGCHLD Workaround

Workarounds for the zsh signal re-entrancy crash (SEGV during exit with p10k), pending or supplementing the zsh 5.9.1-1 upgrade.

**Workaround A — suppress job notifications:**
```zsh
setopt NO_NOTIFY
```
Add near the top of `.zshrc` before p10k loads. Reduces SIGCHLD→job-table interaction during exit.

**Workaround B — block SIGCHLD during exit hooks:**
```zsh
zshexit_functions+=(_block_chld_exit)
_block_chld_exit() { trap '' CHLD; }
```
Add before the p10k source line. Prevents SIGCHLD from re-entering job management during exit processing. Use only if the issue persists after the upgrade or as a belt-and-suspenders measure.
