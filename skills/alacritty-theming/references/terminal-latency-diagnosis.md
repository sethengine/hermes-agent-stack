# Terminal Latency Diagnosis — Is It the Emulator or the Shell?

Users often report "Alacritty is slow to process commands" or "typing feels laggy." Before tuning the terminal emulator, rule out **shell configuration overhead** — the most common cause of perceived terminal slowness on zsh systems.

## Diagnostic Checklist

Run these checks in sequence. The answer is almost always the shell, not the terminal.

### 1. Is it startup or per-keystroke?

Two distinct latency sources:

| Latency type | Symptom | Typical cause |
|---|---|---|
| **Startup delay** | Terminal takes >500ms before the prompt appears | Dead plugin init (zinit sourced but unused), dual theme load, stale zcompdump files |
| **Per-keystroke lag** | Characters appear with visible delay after each keypress | Synchronous zsh-syntax-highlighting, synchronous zsh-autosuggestions, p10k git status blocking prompt render |

### 2. Check zsh startup time

```zsh
# Time 10 native zsh starts (no rc files)
for i in $(seq 10); do /bin/zsh -lic exit; done 2>&1 | tail -1

# Time 10 interactive zsh starts (with rc files)
for i in $(seq 10); do /usr/bin/time zsh -lic exit 2>&1; done | awk '{print $1}' | datamash mean 1
```

Slow startup (>200ms) indicates dead weight in `.zshrc`: unused plugin managers, dual themes, or stale completion dumps.

### 3. Check per-keystroke lag sources

Three zsh features block on every keystroke:

| Feature | Fix |
|---|---|
| `zsh-syntax-highlighting` | Replace with `zsh-fast-syntax-highlighting`, or ensure it's loaded last |
| `zsh-autosuggestions` | `ZSH_AUTOSUGGEST_USE_ASYNC=1` before loading |
| p10k git status | `POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS=0.01` (always async) |

### 4. Check for dead plugin managers

zinit, antigen, and other plugin managers sourced but never used are a common pattern:

```zsh
# If zinit is sourced but has no zinit load calls, it's dead weight
grep 'zinit load\|zinit ice\|zinit light' ~/.zshrc || echo "zinit has zero plugin loads"
```

### 5. Check for dual theme load

If using oh-my-zsh + p10k: oh-my-zsh sets `ZSH_THEME` which loads one theme, then p10k immediately replaces it. Set `ZSH_THEME=""` to skip the wasted render:

```zsh
# Current state
grep '^ZSH_THEME=' ~/.zshrc
# Fix — p10k handles the theme rendering
sed -i 's/^ZSH_THEME=.*/ZSH_THEME=""/' ~/.zshrc
```

### 6. Check for stale compdump files

Multiple `~/.zcompdump*` files cause zsh to regenerate on every start or pick stale completion data:

```zsh
ls -la ~/.zcompdump* 2>/dev/null | wc -l
# If >1: clean and regenerate
rm -f ~/.zcompdump*
# A fresh single dump creates on next start
```

### 7. Check oh-my-zsh update prompt

Oh-my-zsh's automatic update check can cause a blocking prompt on terminal start. Disable it:

```zsh
zstyle ':omz:update' mode disabled
```

### 8. Hide duplicate git work

If using both oh-my-zsh's git plugin AND p10k's git status, they both compute git state on every prompt. Disable oh-my-zsh's untracked file check (p10k handles it):

```zsh
DISABLE_UNTRACKED_FILES_DIRTY=true
```

## Common Fix Recipe

A minimal set of changes that resolves most "terminal is slow" reports where zsh is the bottleneck:

```zsh
# Priority fixes (strongest impact first):
ZSH_AUTOSUGGEST_USE_ASYNC=1          # 1. Unblock keystrokes (biggest win)
ZSH_THEME=""                          # 2. Kill dual theme load
POWERLEVEL9K_VCS_MAX_SYNC_LATENCY_SECONDS=0.01  # 3. Always async git status
DISABLE_UNTRACKED_FILES_DIRTY=true    # 4. No duplicate git work
zstyle ':omz:update' mode disabled    # 5. Kill update prompt
POWERLEVEL9K_INSTANT_PROMPT=verbose   # 6. Show prompt before plugins finish
rm -f ~/.zcompdump*                   # 7. Clean stale completion dumps
```

**Before/after:** Startup dropped from ~183ms → ~164ms on a mid-range system with the above recipe. The subjective improvement is larger than the numbers suggest — per-keystroke auto-suggestions no longer block.

## Reverting

Always create a backup before applying changes:

```zsh
cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d-%H%M)
```

Restore with `cp ~/.zshrc.backup.<timestamp> ~/.zshrc`.

## When It IS the Terminal Emulator

After ruling out the shell (steps 1-7 all clear), check:

- **GPU compositor interference** — KWin/VBlank syncing on NVIDIA + Wayland can delay frame presentation. Switch to a different terminal (foot, konsole) — if they're also slow, it's not the terminal.
- **Font rendering bottleneck** — Some fonts with large fallback chains (Nerd Fonts, powerline) render slowly. Try switching to a simpler monospace font.
- **Direct rendering** — Alacritty uses the GPU. Check if `WINIT_UNIX_BACKEND=x11` or `WAYLAND_DISPLAY=wayland-1` for compositor bypass. On X11, check `LIBGL_ALWAYS_SOFTWARE` isn't accidentally set.
