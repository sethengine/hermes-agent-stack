# Terminal Rendering Troubleshooting

Common rendering glitches that appear when theming or reconfiguring Alacritty — and how to fix them.

## Stale Command Text After Ctrl+C (ZLE Plugin Ordering)

**Symptom:** After pressing Ctrl+C to cancel a partially typed command, the cancelled text reappears on the next prompt (or after the next command executes). It looks like the terminal is re-displaying old input.

**Root cause:** `zsh-syntax-highlighting` is loaded **before** another ZLE-wrapping plugin (typically `zsh-autosuggestions` or `zsh-history-substring-search`).

`zsh-syntax-highlighting` hooks into `zle-line-pre-redraw` to recolor the buffer. When another plugin loads after it, both hook the same widget. Their execution order is undefined, and the syntax-highlighting plugin's buffer state can get overwritten by a stale suggestion — causing the cancelled command text to be redrawn as if it were current input.

**Fix:** Ensure `zsh-syntax-highlighting` is the **very last** plugin in the load order.

In Oh My Zsh:

```zsh
# WRONG — syntax-highlighting is 2nd
plugins=(git zsh-syntax-highlighting zsh-autosuggestions zsh-history-substring-search)

# CORRECT — syntax-highlighting is last
plugins=(git zsh-autosuggestions zsh-history-substring-search zsh-syntax-highlighting)
```

This applies regardless of plugin manager (Oh My Zsh, zinit, zplug, etc.). The rule is: **syntax-highlighting must be last because it wraps ZLE widgets, and anything loaded after it breaks the wrapping chain.**

### How to verify

After fixing, open a new terminal and test:
1. Type a partial command: `ls /usr/loc`
2. Press Ctrl+C — the text should clear completely
3. Type and execute something else: `echo hello`
4. The cancelled text should NOT reappear

If it still happens, check for other ZLE-affecting plugins (like `zsh-autopair`, `zsh-completions`, or any custom `zle-line-pre-redraw` hooks) and ensure they all load before syntax-highlighting.

## Colors Don't Match Theme After Import Change

**Symptom:** You change the `import` path in `alacritty.toml` and save, but colors don't update (or update partially).

**Root cause:** Alacritty's live config reload uses inotify on the config file itself, not on imported files. Saving `alacritty.toml` triggers a reload of all config including imports. If only the imported theme file changed, you must also touch/save `alacritty.toml`.

**Fix:** After editing a theme file, save the main config (even without changes) to trigger reload:

```zsh
touch ~/.config/alacritty/alacritty.toml
```

## Font Rendering Artifacts After Theme Change

**Symptom:** Characters look wrong, have gaps, or stale glyphs remain after switching themes.

**Root cause:** Font rasterizer cache doesn't clear on theme change. Usually a GPU compositor issue.

**Fix:**
- Switch to another virtual desktop and back (triggers compositor repaint)
- Or restart Alacritty
