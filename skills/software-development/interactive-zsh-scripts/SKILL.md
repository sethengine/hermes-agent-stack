---
name: interactive-zsh-scripts
description: Build interactive TUI-style scripts in pure zsh — search, filter, select, preview, and apply patterns. No external dependencies (no fzf, whiptail, gum). For terminal config tools, theme switchers, dotfile managers, and any task needing an interactive menu in a shell environment.
category: software-development
triggers:
  - interactive
  - zsh script
  - TUI
  - theme switcher
---

# Interactive Zsh Scripts

A pattern for building interactive terminal scripts in **pure zsh** — no fzf, gum, dialog, or Node.js needed. Uses zsh built-ins: `print -P` (prompt expansion), `read -r`, arrays, and `grep`/`sed` for search and config editing.

## Core Pattern: Search → Filter → Select → Apply

```
while true; do
  read search query     # Get search input
  filter array with grep # Narrow results
  show numbered list     # Display with print -P
  read selection number  # Get numeric choice
  apply via sed        # Edit config file, trigger live reload
end
```

## Critical Pitfalls

### `print -P` interprets prompt escapes, NOT printf format specifiers

**WRONG** — `%2d` is "last 2 directory components" in zsh prompt expansion, not an integer format:
```zsh
print -P "  %F{blue}%2d.%f ${item}" "$i"   # BUG: prints /home/user/ instead of the number
```

**RIGHT** — embed the number via `$(printf ...)` or `$((r:2:))` padding:
```zsh
print -P "  %F{blue}$(printf '%2d' $i).%f ${item}"
```

Common prompt escapes to watch out for: `%d` (directory), `%n` (username), `%m` (hostname), `%t` (time), `%*` (date+time). When you see unexpected paths or timestamps in your output, you've hit this.

### `local` inside `while` loops at file scope

`local` is only valid inside functions. A `while` loop at the top level of a script cannot use `local`:
```zsh
while true; do
  local x="value"   # BUG: parse error in zsh
done
```
Use plain variable assignment instead:
```zsh
while true; do
  x="value"         # OK: global scope
done
```

### `read -r` with prompt string

zsh syntax: `read -r "?Prompt: " var` (note `"?"` prefix, quotes around the whole argument containing the prompt).

Bash syntax for comparison: `read -r -p "Prompt: " var`.

### Safe sed pattern for replacing a path in a TOML/YAML import line

```zsh
# Matches any double-quoted string ending in .ext within an import block.
# Works with both ~/path and /absolute/path.
# Handles multi-line import blocks (only touches the line with the file path).
sed -i 's|"[^"]*\.ext"|"'"$new_file"'"|' "$CONFIG"
```

Use `|` as sed delimiter to avoid escaping `/` in file paths. This pattern replaces the first quote-delimited path ending in `.ext` — safe for config files where the import is the only `.ext` path.

### NEVER source interactive scripts from shell rc files

**This is the most destructive mistake with interactive scripts.** Adding a bare path to `.zshrc`/`.bashrc`/`.profile`:

```zsh
# ~/.zshrc — WRONG
~/.config/something/theme-switcher.zsh
```

causes ALL these failures at every shell start:

- **`print -P` floods the terminal** — Escape codes and literal `%` characters appear before every prompt. `%F{color}` renders as prompt escapes or literal `%` depending on context, producing garbage.
- **fzf / TUI tools try to launch** — During rc-file execution, stdin is not a proper TTY, causing fzf to fail, hang, or dump errors.
- **Config files get clobbered** — The script's `sed` commands run on every shell start, potentially overwriting config with stale values.

**How to offer an interactive script instead:**
```zsh
# Add an alias — user must type it to activate
alias myscript='/path/to/script.zsh'

# Or a shell function
myscript() { /path/to/script.zsh "$@"; }
```

**How to fix if already broken (terminal shows `%` and garbage):**
```bash
# Blind-type this from a working terminal:
sed -i '/theme-switcher/d' ~/.zshrc
# Then open a new terminal
```

## Optional Upgrade: fzf Integration

For large item lists (50+), the numbered-menu approach becomes unwieldy. fzf adds fuzzy search, a live preview pane, and instant-apply on scroll.

### Pattern: separate helper scripts for fzf to call

fzf's `--preview` and `--bind` run subprocesses that cannot call zsh functions from the parent script. Split into three files:

| File | Purpose |
|------|---------|
| `launcher.zsh` | Builds the list, launches fzf, handles cleanup |
| `apply.sh` | Silent apply (called by `execute-silent`) — just sed the config |
| `preview.sh` | Rich preview for fzf's pane — show color swatches, file contents, screenshots |

### Applying on focus change (live-switch)

The key pattern for instant-apply as the user scrolls:

```zsh
fzf --bind="focus:execute-silent(bash apply.sh {})"
```

`{}` is fzf's placeholder for the currently highlighted item. `execute-silent` runs the command without blocking the UI.

### Toggle live mode with flag file + transform-header

```zsh
touch /tmp/live-flag

fzf \
  --bind="focus:execute-silent(
    if [ -f /tmp/live-flag ]; then bash apply.sh {}; fi
  )" \
  --bind="ctrl-l:execute-silent(
    if [ -f /tmp/live-flag ]; then rm /tmp/live-flag; else touch /tmp/live-flag; fi
  )+transform-header(
    if [ -f /tmp/live-flag ]; then echo 'LIVE — themes switch on scroll'; else echo 'PAUSED — browse only'; fi
  )"
```

Note: `transform-header` requires fzf 0.48+ (uses a shell command to produce the header string dynamically). `execute-silent` requires fzf 0.22+.

## Script Structure Template

```zsh
#!/usr/bin/env zsh

# ── Config ──────────────────────────────────────
ITEMS_DIR="$HOME/.config/something/items"
CONFIG="$HOME/.config/something/config.toml"

# ── Load items ──────────────────────────────────
items=($(ls "$ITEMS_DIR"/*.ext | xargs -n1 basename | sed 's/\.ext$//' | sort))
total=${#items}

# ── Detect current selection ────────────────────
current_item() {
  local line
  line=$(grep 'pattern' "$CONFIG" | head -1)
  echo "$line" | sed -n 's/.*regex_to_extract_name.*/\1/p'
}

# ── Apply selection ─────────────────────────────
apply_item() {
  local name="$1"
  local file="$ITEMS_DIR/$name.ext"
  [[ ! -f "$file" ]] && return 1
  sed -i 's|"[^"]*\.ext"|"'"$file"'"|' "$CONFIG"
  print -P "%F{green}✔ Applied: %f$name"
}

# ── Interactive loop ────────────────────────────
search=""
filtered=("${items[@]}")

while true; do
  # Step 1: Get search/filter from user
  print "Enter a letter to filter, a word to search, or Enter for all:"
  read -r "?→ " search
  [[ "$search" == "q" ]] && exit 0

  # Step 2: Filter array
  if [[ "$search" =~ ^[a-zA-Z]$ ]]; then
    filtered=($(printf '%s\n' "${items[@]}" | grep -i "^$search"))
  elif [[ -n "$search" ]]; then
    filtered=($(printf '%s\n' "${items[@]}" | grep -i -- "$search"))
  fi

  # Step 3: Show numbered menu
  count=${#filtered}
  for i in $(seq 1 $count); do
    print -P "  %F{blue}$(printf '%2d' $i).%f ${filtered[$i]}"
  done

  # Step 4: Get selection
  read -r "?Select number: " sel
  if [[ "$sel" =~ ^[0-9]+$ ]] && (( sel >= 1 && sel <= count )); then
    choice="${filtered[$sel]}"
    apply_item "$choice"
  fi
done
```

## Color Reference for `print -P`

| Code | Effect |
|------|--------|
| `%F{red}text%f` | Red foreground |
| `%F{green}text%f` | Green foreground |
| `%F{blue}text%f` | Blue foreground |
| `%F{cyan}text%f` | Cyan foreground |
| `%F{yellow}text%f` | Yellow foreground |
| `%Btext%b` | Bold |
| `%Utext%u` | Underline |

## ANSI Color reference for `printf` / `echo -e`

| Code | Color |
|------|-------|
| `\033[30m` | Black |
| `\033[31m` | Red |
| `\033[32m` | Green |
| `\033[33m` | Yellow |
| `\033[34m` | Blue |
| `\033[35m` | Magenta |
| `\033[36m` | Cyan |
| `\033[37m` | Light gray |
| `\033[90m` | Dark gray |
| `\033[91-97m` | Light variants |
| `\033[39m` | Default fg |
| `\033[49m` | Default bg |
| `\033[48;2;R;G;Bm` | True-color background (R, G, B = 0-255) |

## See Also

- `templates/alacritty-theme-switcher.zsh` — full working example: 168 Alacritty themes, search by letter/word, numbered selection, live config reload via sed, color palette preview.
- `templates/theme-apply.sh` — silent apply helper for fzf's focus:execute-silent pattern. Called as a subprocess by fzf to apply the highlighted item without blocking the UI.
- `alacritty-theming` skill — Alacritty color format reference, palette design principles, switching methods.
