---
source_session: "20260425_181102_a0ddba"
category: software
tags: [hermes, terminal, ansi, coloring, syntax-highlighting]
---

# Hermes ANSI Terminal Coloring

Hermes CLI outputs plain text — it has no built-in Markdown rendering or auto-syntax highlighting. Two approaches add color:

## 1. ANSI Escape Codes (native, works interactively)

Embed codes directly in responses. Hermes' system prompt can be configured to prefer colored output.

| Effect | Code |
|--------|------|
| Reset | `\033[0m` |
| Red/Green/Yellow/Blue/Magenta/Cyan/White | `\033[31m`–`\033[37m` |
| Bright variants | `\033[9Xm` (e.g., `\033[92m` bright green) |
| Background | `\033[41m` etc. |

Best for **interactive chat** where piping blocks stdin.

## 2. `bat` via pipe (non-interactive)

For scripts, logs, and batch queries, pipe Hermes output through `bat`:

```bash
# Alias for zsh
alias hermes-bat='hermes | bat --color=always --style=plain --paging=never'
```

- `--style=plain`: no line numbers, header, or grid
- The `--line-numbers` flag does NOT exist in bat (it's part of `--style`)
- Auto-detects syntax for code blocks; `--language=py` or `--language=md` for explicit

Non-interactive only — piping blocks chat input.

## Key distinction

- **`bat`/`glow`**: pipe-based, non-interactive only
- **ANSI codes**: work in live chat, embedded directly in responses
- **No Hermes config option** enables auto-highlighting for all output

Related: [[hermes-desktop-font-system]], [[hermes-mcp-server-troubleshooting]]
