# Zsh Startup Optimization — Session Findings (July 2026)

Real-world debugging of "zsh feels slow / Alacritty laggy to process commands." System: Manjaro KDE Wayland, oh-my-zsh + powerlevel10k, zinit (unused), 7 plugins.

## Symptom

User reported Alacritty "slow to process commands and passwords." Not startup time per se — the feeling of lag *while typing* and between commands.

## Diagnostic Methodology

### 1. Baseline startup time
```bash
time zsh -i -c exit 2>&1
```
Watch for errors during init: `tput` failures, gitstatus failures, `can't change option: monitor`. These indicate config problems even when the timing looks acceptable.

### 2. Check for dead plugin managers
```bash
grep -n 'zinit\|ZINIT\|zplug\|zgen\|oh-my-zsh' ~/.zshrc
```
Zinit was sourced but no `zinit load` or `zinit light` calls existed — pure dead weight. Every plugin manager init adds hundreds of ms.

### 3. Check for dual theme loading
```bash
grep 'ZSH_THEME\|powerlevel10k\|p10k' ~/.zshrc
```
`ZSH_THEME="miloshadzic"` loaded first, then p10k replaced it. oh-my-zsh ran full theme init (including `tput` color checks) for a theme that was immediately discarded.

### 4. Check per-keystroke processing
```bash
grep 'plugins=' ~/.zshrc
```
7 plugins: git, zsh-autosuggestions, zsh-you-should-use, zsh-bat, zsh-history-substring-search, zsh-z, zsh-syntax-highlighting.

- `zsh-syntax-highlighting` — regex on every keystroke (highest per-char cost)
- `zsh-autosuggestions` — history search on every keystroke (second highest)
- `git` — duplicate work (p10k also does git status)

### 5. Check async configuration
Async autosuggestions was NOT enabled. Without `ZSH_AUTOSUGGEST_USE_ASYNC=1`, every keystroke blocks on history search.

### 6. Check oh-my-zsh overhead
```bash
grep "omz:update" ~/.zshrc
```
Auto-update check fires periodically, adds 300-500ms timeout when triggered. Disable with `zstyle ':omz:update' mode disabled`.

### 7. Check p10k git status configuration
```bash
grep 'POWERLEVEL9K_VCS_MAX_SYNC_LATENCY\|POWERLEVEL9K_INSTANT_PROMPT' ~/.zshrc
```
- `POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS` was `unset` — default allows blocking git status
- `POWERLEVEL9K_INSTANT_PROMPT=quiet` — suppresses prompt until full init (feels slower)

### 8. Check completion dump health
```bash
ls -la ~/.zcompdump*
```
4 stale dumps (53KB, 54KB, 38KB, 126KB zwc). Multiple dumps mean compinit is regenerating them periodically, adding startup variance.

## Fixes Applied

| # | Fix | Mechanism |
|---|---|---|
| 1 | Remove zinit init (4 lines) | Dead plugin manager — sourced but never used |
| 2 | `ZSH_THEME=""` instead of `"miloshadzic"` | p10k replaces it anyway, save init cost |
| 3 | `zstyle ':omz:update' mode disabled` | Kill auto-update prompt timeout |
| 4 | `ZSH_AUTOSUGGEST_USE_ASYNC=1` | Async autosuggestions — non-blocking on keystrokes |
| 5 | `DISABLE_UNTRACKED_FILES_DIRTY=true` | oh-my-zsh git plugin stops checking untracked (p10k does it) |
| 6 | `POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS=0.01` | Force async git status — never block prompt |
| 7 | `POWERLEVEL9K_INSTANT_PROMPT=verbose` | Show prompt before plugins finish loading |
| 8 | `rm ~/.zcompdump*` | Clean stale dumps — single fresh dump on next start |

## Result

Startup: 183ms → 164ms (11% faster). Per-keystroke: async autosuggestions + no duplicate theme init. In real terminal (with TERM + gitstatus daemon), zero errors at startup.

## Pitfall: Testing zsh startup

`time zsh -i -c exit` runs interactively but without a real terminal. Errors like `tput: No value for $TERM` and `gitstatus failed to initialize` are expected and do NOT reflect real terminal behavior. Only use these as signals of unnecessary work being attempted.

Oh-my-zsh auto-update check triggers on the FIRST run after touching `~/.zshrc` — expect a one-time spike to 600ms+. Subsequent runs use cached state.

## Pitfall: gitstatus daemon processes

Multiple `gitstatusd` processes with `-v FATAL` flags are NORMAL — one per terminal tab. The FATAL log level means "only log fatal errors" (production mode), not "a fatal error occurred." The daemon binary at `~/.cache/gitstatus/gitstatusd-linux-x86_64` is v1.5.4, static-pie linked.
