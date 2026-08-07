#!/usr/bin/env bash
# Theme Apply — silent apply helper for fzf's execute-silent
# Usage: ./theme-apply.sh <theme_name>
# Pattern: fzf --bind="focus:execute-silent(bash apply.sh {})"
#
# Modify THEMES_DIR / CONFIG for your own use case.

name="$1"
theme_file="$HOME/.config/alacritty/themes/themes/$name.toml"
config="$HOME/.config/alacritty/alacritty.toml"

[[ -f "$theme_file" ]] || exit 1
sed -i 's|"[^"]*\.toml"|"'"$theme_file"'"|' "$config" && echo "$name"
