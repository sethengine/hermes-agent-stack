---
source_session: 20260520_232547_483a60
extracted: 2026-07-17
category: software
tags: [alacritty, shell, performance, zsh, powerlevel10k, nvm, latency]
---

# Alacritty and Shell Speed Optimization

## Alacritty Config Optimizations

For Wayland + NVIDIA:

```toml
[env]
WINIT_UNIX_BACKEND = "wayland"

[window]
decorations = "None"
dynamic_padding = false
opacity = 1.0  # disable transparency

[selection]
save_to_clipboard = false  # reduce clipboard overhead

[cursor]
style = "Block"
```

## Shell Startup Bottlenecks

Common bottlenecks in `~/.zshrc`:

- **Oh My Zsh with multiple plugins** — heavy framework loading
- **Powerlevel10k gitstatus daemon failing** — falls back to slow git queries (add `POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=0` to fix)
- **nvm loading every shell** — lazy-load with a function wrapper: define `nvm()` that defers loading until first use
- **compinit** — completion cache regeneration overhead
- **zinit installed but unused** — loads framework but uses OMZ anyway (waste)

## Fix: Powerlevel10k Gitstatus Failure

Add to `~/.zshrc` before powerlevel10k instant prompt:

```zsh
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=0
typeset -g POWERLEVEL9K_VCS_DISABLED_WORKDIR_PATTERN='~'
```

## Fix: Lazy-Load nvm

Replace direct source with a lazy function:

```zsh
export NVM_DIR="$HOME/.nvm"
nvm() { unset -f nvm; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"; nvm "$@"; }
node() { unset -f node nvm; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"; node "$@"; }
```
