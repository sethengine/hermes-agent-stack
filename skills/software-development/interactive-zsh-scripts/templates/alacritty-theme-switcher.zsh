#!/usr/bin/env zsh
# =============================================================================
# Alacritty Theme Switcher — pure zsh, no external dependencies
# =============================================================================
# Full working example of the interactive-zsh-scripts pattern.
# Browse 168 themes by letter or keyword, preview color palettes, apply instantly.
#
# This is a TEMPLATE — modify ITEMS_DIR and CONFIG for your own use case.
#
# To use:  ~/.config/alacritty/theme-switcher.zsh
# NEVER add a bare path to .zshrc — create an alias instead:
#   alias themes='~/.config/alacritty/theme-switcher.zsh'

CONFIG="$HOME/.config/alacritty/alacritty.toml"
THEMES_DIR="$HOME/.config/alacritty/themes/themes"
PRINT_COLORS="$HOME/.config/alacritty/themes/print_colors.sh"

# ── Error handling ──────────────────────────────────────────────────
if [[ ! -d "$THEMES_DIR" ]]; then
  print -P "%F{red}✘ Theme directory not found: $THEMES_DIR%f"
  exit 1
fi
if [[ ! -f "$CONFIG" ]]; then
  print -P "%F{red}✘ Config not found: $CONFIG%f"
  exit 1
fi

# ── Load theme list ─────────────────────────────────────────────────
themes=($(ls "$THEMES_DIR"/*.toml | xargs -n1 basename | sed 's/\.toml$//' | sort))
total=${#themes}

# ── Get current theme from the import line ──────────────────────────
current_theme() {
  local line
  line=$(grep '\.toml' "$CONFIG" | head -1)
  echo "$line" | sed -n 's/.*\/\(.*\)\.toml.*/\1/p'
}

# ── Apply a theme by name ──────────────────────────────────────────
apply_theme() {
  local name="$1"
  local file="$THEMES_DIR/$name.toml"
  [[ ! -f "$file" ]] && return 1
  # Replace the first quote-delimited .toml path in the config
  sed -i 's|"[^"]*\.toml"|"'"$file"'"|' "$CONFIG"
  print -P "%F{green}✔ %f$name"
}

# ── Show color palette ──────────────────────────────────────────────
show_palette() {
  [[ -x "$PRINT_COLORS" ]] && bash "$PRINT_COLORS"
}

# ── Main interactive loop ──────────────────────────────────────────
clear
print -P "%F{cyan}╔══════════════════════════════╗%f"
print -P "%F{cyan}║  Alacritty Theme Switcher    ║%f"
print -P "%F{cyan}║  $total themes available      ║%f"
print -P "%F{cyan}╚══════════════════════════════╝%f"
echo ""

current=$(current_theme)
[[ -n "$current" ]] && print -P "Current: %F{green}$current%f" && echo ""

search=""
filtered=("${themes[@]}")

while true; do
  if [[ -z "$search" ]]; then
    print "Enter a letter to filter, a word to search, or Enter for all (q=quit):"
    read -r "?→ " search
    echo ""
    [[ "$search" == "q" ]] && print -P "%F{yellow}Goodbye.%f" && exit 0
  fi

  # Filter
  if [[ -z "$search" ]]; then
    filtered=("${themes[@]}")
  elif [[ "$search" =~ ^[a-zA-Z]$ ]]; then
    filtered=($(printf '%s\n' "${themes[@]}" | grep -i "^$search"))
  else
    filtered=($(printf '%s\n' "${themes[@]}" | grep -i -- "$search"))
  fi

  count=${#filtered}
  if [[ $count -eq 0 ]]; then
    print -P "%F{red}No matches for \"$search\"%f"
    search=""
    continue
  fi

  # Show numbered list
  print -P "%F{cyan}Matches ($count):%f"
  for i in $(seq 1 $count); do
    marker=""
    [[ "${filtered[$i]}" == "$current" ]] && marker="  ← current"
    print -P "  %F{blue}$(printf '%2d' $i).%f ${filtered[$i]}%f$marker"
  done
  echo ""

  read -r "?Select number (Enter=new search, q=quit): " sel
  [[ "$sel" == "q" ]] && print -P "%F{yellow}Goodbye.%f" && exit 0

  if [[ -z "$sel" ]]; then
    search=""
    clear
    continue
  fi

  if [[ "$sel" =~ ^[0-9]+$ ]] && (( sel >= 1 && sel <= count )); then
    choice="${filtered[$sel]}"
    clear
    apply_theme "$choice"
    sleep 0.1  # Let live reload catch up
    show_palette
    current="$choice"
    echo ""
    print -P "%F{yellow}[Enter to continue, or Ctrl+C]%f"
    read -r -s
    clear
  else
    print -P "%F{red}Invalid%f"
    sleep 0.5
  fi
done
