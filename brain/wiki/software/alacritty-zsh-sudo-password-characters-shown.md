---
source_session: 20260719_174428_5a4567
date: 2026-07-19
category: software
tags: [alacritty, zsh, sudo, password-input, terminal-troubleshooting]
---

# Alacritty + Zsh: Password Characters Appear at sudo Prompt

Diagnostic notes from an unresolved issue where typing at the `sudo` password prompt in [[alacritty]] with [[zsh]] shows the typed characters on screen (abnormal) and the password is rejected.

## Symptoms

- Characters **appear on screen** at the sudo password prompt (normal behavior is a blank field with no echo)
- The password is rejected
- Issue is specific to `sudo` prompts — other password prompts work fine

## Diagnostic Steps (no resolution found)

1. **Clear cached sudo credentials** — `sudo -k` forces sudo to re-authenticate from scratch
2. **Check if characters are being echoed by sudo or by the shell** — visible characters at a sudo prompt indicate the terminal or shell is interfering with password input mode
3. **Suspect causes to investigate:**
   - `TERM` environment variable mismatch (sudo may fall back to echo mode if terminal type is unrecognized)
   - ZLE plugin interference ([[zsh-syntax-highlighting]] or [[zsh-autosuggestions]] hooking into password prompts)
   - Stty settings — `stty -echo` not being properly set by sudo
   - Sudo configuration (`sudo -K`, `env_reset`, `env_keep` affecting terminal settings)

## Related

- [[alacritty-config-best-practices]]
- [[zsh-performance-tuning]]
- [[terminal-password-echo-issues]]
