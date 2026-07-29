# Invisible Mouse Cursor on NVIDIA + Wayland + KDE

## Symptom

Cursor works (click targets still register) but the pointer sprite is invisible. The loading/busy cursor (app icon) is visible briefly when launching applications, but the normal `left_ptr` pointer never renders.

## Root Causes

| Cause | When | Fix |
|-------|------|-----|
| NVIDIA hardware cursor plane glitch | Driver 595+ beta, especially with non-standard cursor themes | `KWIN_FORCE_SW_CURSOR=1` — forces KWin to render cursor via compositor instead of hardware plane |
| Missing/wrong cursor theme assets | Custom themes like `pixelfun3` may lack Wayland cursor assets | Switch to a standard theme: `Breeze_Light`, `breeze_cursors`, or `Adwaita` |
| `libxcb-cursor.so.0` not found | Qt xcb platform plugin can't load cursor — affects XWayland fallback paths | Install `xcb-util-cursor` (check first: `pacman -Q xcb-util-cursor`) |

## Fix Procedure

### 1. Set KWIN_FORCE_SW_CURSOR=1

Three layers to ensure it persists:

```bash
# Layer A — systemd --user (immediate effect after restart)
systemctl --user set-environment KWIN_FORCE_SW_CURSOR=1

# Layer B — environment.d (survives login)
mkdir -p ~/.config/environment.d
echo 'KWIN_FORCE_SW_CURSOR=1' > ~/.config/environment.d/kwin_sw_cursor.conf

# Layer C — plasma-workspace env (alternative sourcing)
mkdir -p ~/.config/plasma-workspace/env
cat > ~/.config/plasma-workspace/env/cursor_fix.sh << 'EOF'
#!/usr/bin/env bash
export KWIN_FORCE_SW_CURSOR=1
EOF
chmod +x ~/.config/plasma-workspace/env/cursor_fix.sh
```

### 2. Apply live (no logout)

```bash
export KWIN_FORCE_SW_CURSOR=1
systemctl --user import-environment KWIN_FORCE_SW_CURSOR
systemctl --user restart plasma-kwin_wayland.service
```

### 3. Switch cursor theme

```bash
plasma-apply-cursortheme Breeze_Light
# Verify
kreadconfig5 --file ~/.config/kcminputrc --group Mouse --key cursorTheme
```

### 4. Verify

```bash
qdbus6 org.kde.KWin /KWin supportInformation | grep -A5 'Cursor'
# Should show: themeName and themeSize
```

## Pitfalls

### DO NOT restart KWin via `systemctl restart` without warning

On Wayland, KWin **is the display server**. `systemctl restart plasma-kwin_wayland.service`:

1. KWin stops → compositor dies → **screen goes black**
2. SDDM (UID 959) grabs the GPU
3. The user session never respawns → **stays black permanently**
4. This is expected Wayland behavior, NOT a crash — but it looks identical to one

**Always ask the user before restarting KWin.** Use `systemctl --user import-environment` + restart as above for live env changes.

### Hard vs Software cursor tradeoffs

| Mode | Cursor visible? | Performance |
|------|----------------|-------------|
| `KWIN_FORCE_SW_CURSOR=0` (hw cursor) | May be invisible on NVIDIA 595+ | Best — no compositor overhead |
| `KWIN_FORCE_SW_CURSOR=1` | Always visible | Slightly higher GPU load from compositor cursor rendering |

If software cursor causes instability (rare), revert:
```bash
systemctl --user unset-environment KWIN_FORCE_SW_CURSOR
systemctl --user set-environment KWIN_FORCE_SW_CURSOR=0
```
Then **ask the user to log out/in** to apply.

### Cursor theme detection

KWin reads cursor theme from KDE settings (`kcminputrc`), not `XCURSOR_THEME` env var. Changing the env var alone does nothing.

### EDID firmware loading failure

If the kernel cmdline has `drm.edid_firmware=DP-3:edid/hp-x34.bin`, the NVIDIA 595 driver may fail to load it (`firmware load for edid/hp-x34.bin failed with error -2`). This is logged at boot but is **not** the cause of invisible cursor — the monitor still works with its default EDID.
