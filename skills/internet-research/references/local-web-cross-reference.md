# Local + Web Cross-Reference Research

For system configuration research — combine local system inspection with web research to find what's actually configured vs what the current best practice is.

## When to Use This Pattern

- Investigating why a feature isn't working (GPU acceleration, HW decode, audio)
- Auditing system configuration against current best practices
- Diagnosing why a service behaves differently than expected
- Upgrading software and needing to know if flags/settings have changed

## Methodology

### Phase 1: Establish Current State (Local)

Use terminal + file tools to snapshot what's actually running:

```python
# What processes are active and with what flags?
terminal("ps aux | grep chrome | grep -v grep")
# The command line in /proc/pid/cmdline is the ground truth

# What packages are installed and what version?
terminal("pacman -Q libva-nvidia-driver google-chrome nvidia-utils")

# What config files exist?
# Desktop files (system vs user-local):
#   /usr/share/applications/.desktop — system default
#   ~/.local/share/applications/.desktop — user override (takes priority)
# Wrapper scripts:
#   /usr/bin/google-chrome-stable — often a bash wrapper that reads a flags file
#   ~/.config/chrome-flags.conf — persistent Chrome flags

# What env vars are set where?
# Search: ~/.profile, ~/.bashrc, ~/.zshrc, /etc/environment,
#         ~/.config/environment.d/*.conf, desktop file Exec lines

# What drivers/libraries are installed (for GPU/audio/etc)?
terminal("ls /usr/lib/dri/*nvidia*")
terminal("vainfo")
terminal("nvidia-smi --query-gpu=name,driver_version --format=csv")

# What actual features does the running process have?
# For Chrome: inspect chrome://gpu or check child GPU process flags
terminal("cat /proc/$(pgrep -f 'chrome --type=gpu-process' | head -1)/cmdline")
```

### Phase 2: Research Current Best Practices (Web)

```python
# Use x_search as fallback when web_search is unavailable
x_search("topic best practices Wayland NVIDIA 2026")
x_search("topic deprecated flag removed version")

# Primary sources
# Arch Wiki: curl "https://wiki.archlinux.org/title/Topic?action=raw"
# Official docs: README from GitHub repos
# Package changelogs / release notes

# Cross-reference: flag was removed, deprecation notice, replacement
```

Key questions to answer in this phase:
- What is the *current* recommended configuration?
- Were specific flags deprecated/removed in recent versions?
- Are there known bugs or regressions with certain combos?
- What do other users report working?

### Phase 3: Compare & Gap Analysis

```markdown
## Current Setup
| Component | Value |
|-----------|-------|
| Chrome version | 149.x |
| Driver version | 595.x |
| VA-API driver | libva-nvidia-driver 0.0.17 |
| chrome-flags.conf | --flag-a, --flag-b |
| Desktop file Exec | env FOO=bar /usr/bin/chrome |

## Issues Found
1. **Flag X removed in v148** — using deprecated flag Y instead of Z
2. **Wrong driver override** — desktop file sets LIBVA_DRIVER_NAME=wrong
3. **Missing workaround** — env var that fixes power consumption not set

## Recommended Changes
- Replace `--flag-old` with `--flag-new`
- Fix desktop file Exec line
- Add missing env var
```

## Common Sources for System Research

| What to check | Where | How |
|--------------|-------|-----|
| Chrome flags wrapper | `/usr/bin/google-chrome-stable` | Bash script, reads `~/.config/chrome-flags.conf` |
| Chrome persistent flags | `~/.config/chrome-flags.conf` | One flag per line |
| Desktop launcher | `~/.local/share/applications/*.desktop` | Overrides system version |
| System desktop launcher | `/usr/share/applications/*.desktop` | Default, not edited |
| Environment vars | `~/.profile`, `~/.config/environment.d/` | KDE Plasma sources these on login |
| Running process args | `/proc/$pid/cmdline` | Ground truth — includes all effective flags |
| Chrome GPU status | `chrome://gpu` | Shows actual feature enable/disable |
| Package versions | `pacman -Q` | Exact version numbers |
| X community knowledge | x_search | Current issues, workarounds |
| Arch Wiki | curl or web_extract on `?action=raw` | Linux best practices |
