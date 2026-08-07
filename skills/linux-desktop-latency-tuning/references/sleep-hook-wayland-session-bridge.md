# systemd-sleep Hooks Run as Root — Bridging into the Wayland Session

Session: display stayed black after sleep/wake; user rebooted. Root cause was NOT the
GPU — it was the `/usr/lib/systemd/system-sleep/latency-fix` resume hook silently
failing to re-sync the display.

## The Core Rule

`systemd-sleep` executes hooks (and systemd services generally) **as root**. Root has
no access to the user's Wayland session:

- no `WAYLAND_DISPLAY` set
- no `XDG_RUNTIME_DIR=/run/user/<uid>` (root's is `/run/user/0`)
- no access to the user's D-Bus session bus

Any GUI-ish command run from a root hook (`kscreen-doctor`, `qdbus*`, `kwriteconfig6`
for session files, `systemctl --user ...`) fails silently — especially when the script
uses `2>/dev/null`, which is the norm in these hooks.

## Error Signatures (all stderr-suppressed in typical hooks)

```
kscreen-doctor: could not connect to display
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in ""
qdbus: could not connect to display
```

The hook did not crash the resume; it just did nothing, so the DP link was never
re-driven → black screen → user rebooted (looks like "sleep broke my display").

## Diagnosis Path

1. `journalctl --list-boots` — confirm the "resume" was actually a fresh boot.
2. `journalctl -b <prev> --no-hostname | grep -iE "kscreen|qdbus|qt.qpa|latency-fix"` —
   find the silent display failures in the previous boot's post-resume window.
3. Note the hook runs as root while the display lives in the user session.

## The Fix — runuser Bridge

Wrap every session-dependent command in a helper that injects the user's session env:

```bash
USER_UID=$(id -u sethengine 2>/dev/null || echo 1000)
USER_RUN=/run/user/$USER_UID
WAY_DISP=$(ls "$USER_RUN"/wayland-* 2>/dev/null | head -1 | xargs -r basename || echo wayland-0)
run_as_user() {
    runuser -u sethengine -- env \
        XDG_RUNTIME_DIR="$USER_RUN" \
        WAYLAND_DISPLAY="$WAY_DISP" \
        QT_QPA_PLATFORM=wayland \
        "$@" 2>/dev/null
}
```

Then: `run_as_user kscreen-doctor output.DP-3.disable` etc.
Add `sleep 2` between disable → enable → mode-set; the DP link needs time.

## qdbus vs qdbus6

`qdbus` on this system only exists at `/usr/lib/qt6/bin/qdbus` — **not on PATH** for
root or non-interactive shells. Always use `qdbus6` (at `/usr/bin/qdbus6`):

```bash
run_as_user qdbus6 org.kde.KWin /Compositor active   # prints "true" when reachable
```

## Testing Without Root

`runuser` refuses non-root callers, but you can validate the exact env proxy by running
the same `env ...` command as the user:

```bash
env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland \
    kscreen-doctor --outputs
# Should list DP-3 with full mode list and exit 0

env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland \
    qdbus6 org.kde.KWin /Compositor active
# Should print "true"
```

## Verify After Install

```bash
md5sum /usr/lib/systemd/system-sleep/latency-fix /home/<user>/latency-fix.fixed   # must match
bash -n /usr/lib/systemd/system-sleep/latency-fix
```

The full known-good hook lives in SKILL.md section 9.
