---
source: "session_20260704_175147_58c619"
date: "2026-07-05"
category: "software"
tags: [emacs, doom-emacs, keybindings, pure-emacs, workspace, projectile]
related: [[doom-emacs-ide-setup.md]], [[doom-emacs-evil-ergonomics.md]]
---

# Doom Emacs Pure Emacs Keybindings (No Evil)

Doom Emacs used without Evil mode (evil-everywhere disabled) relies on standard Emacs keybindings:

## Buffer & Window Management
| Key | Action |
|-----|--------|
| `C-x b` | Switch buffer |
| `C-x C-b` | List all buffers |
| `C-x o` | Next window |
| `C-x 0` | Close current window |
| `C-x 1` | Keep only this window |
| `C-x 2` | Split horizontal |
| `C-x 3` | Split vertical |
| `C-x k` | Kill buffer |

## File & Project
| Key | Action |
|-----|--------|
| `C-x C-f` | Find file |
| `C-x p f` | Find file in project |
| `C-x p p` | Switch project |
| `C-x p b` | Switch buffer in project |

## Workspaces (persp-mode)
Doom Emacs provides virtual desktops via `M-x +workspace/<action>`: `new`, `switch-to`, `rename`, `kill`, `display`, `save`, `load`. Switch between workspaces preserves window layout and open files per workspace.
