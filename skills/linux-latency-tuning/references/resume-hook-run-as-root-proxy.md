# Resume Hooks Run as Root — Session-Bound Display Commands Need a Proxy

Source: black-screen-after-suspend/resume debugging, Aug 2026, KDE Wayland + NVIDIA.

## Why resume display commands silently do nothing

`/usr/lib/systemd/system-sleep/*` hooks execute as **root** with a bare environment.
Two independent reasons a `kscreen-doctor`/DBus/KWin call inside the hook can fail even
when it works perfectly from the user's terminal:

1. **No session context** — as root, there is no `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`,
   or `DISPLAY` pointing at the user's plasma session. A display command either errors
   or touches the wrong (non-existent) display.
2. **`qdbus` is not on PATH for root** — the `qdbus` name only exists at
   `/usr/lib/qt6/bin/qdbus`, which is NOT in the non-interactive root PATH. The working
   binary is **`qdbus6`** at `/usr/bin/qdbus6`. A hook that calls `qdbus` (or resolves
   `which qdbus`) silently finds nothing.

## The fix: wrap session commands in `runuser` and use `qdbus6`

```bash
case "$1" in
  post)
    # Restore display/output config in the user's session (not as root's env)
    runuser -u sethengine -- env \
      XDG_RUNTIME_DIR=/run/user/$(id -u sethengine) \
      WAYLAND_DISPLAY=wayland-1 DISPLAY=:1 \
      /usr/bin/kscreen-doctor -o   # or restore toolkit commands
    # Verify compositor is up — MUST use qdbus6, not qdbus
    runuser -u sethengine -- qdbus6 org.kde.KWin /Compositor \
      org.freedesktop.DBus.Properties.Get org.kde.kwin.Compositing compositingType
    ;;
esac
```

Always test the exact env vars + binary from an interactive shell first before baking them
into the hook — the non-interactive root PATH used by systemd-sleep is far narrower than a
login shell's. `runuser` requires root, which the hook already has.

## Pitfalls
- Distinguish this from the unrelated `$1` vs `$2` argument bug: hooks must `case "$1" in post)`.
  The "runs as root so it misses the session" bug is a SEPARATE failure mode (command runs,
  but touches no live session).
- Put the hook in `/home/<user>/` behind `sudo cp` for the user to install; password prompts
  can't pass through an agent's terminal, so hand the user the exact `sudo cp` line instead of
  trying `sudo` interactively.