# Chrome GPU Backend Validation (NVIDIA + Wayland)

Session: user's desktop-launched Chrome rendered everything in software despite flags. Investigation of valid/invalid ANGLE backends plus a terminal-launch false-negative trap that produced a wrong "nothing works" conclusion (user corrected it).

## Allowed ANGLE backends (Chrome 149 Linux)

`gl_factory.cc` allowed-implementations list (the authoritative set):

```
[(gl=egl-angle,angle=opengl),(gl=egl-angle,angle=opengles),(gl=egl-angle,angle=vulkan)]
```

| Flag | Verdict |
|------|---------|
| `--use-angle=desktop` / `--use-gl=desktop` | **INVALID** — not in allowed list. GPU process requests `(gl=none,angle=none)`, fails, forces `--use-gl=disabled` → software. |
| `--use-angle=vulkan` | Blocked under `--ozone-platform=wayland` (`'--ozone-platform=wayland' is not compatible with Vulkan`); crashes GPU process on NVIDIA+Wayland. |
| `--use-gl=desktop` (native GLX) | Impossible on Wayland — no X11/GLX present. |
| `--use-gl=angle --use-angle=opengl` | Working hardware path on NVIDIA Wayland. |
| `--use-gl=angle` (no `--use-angle`) | ANGLE Wayland default = `egl-angle/opengl` — also works; removing the invalid override is often the fix. |

## The terminal-launch false-negative trap

Launching Chrome from a non-graphical shell (terminal tool, background process, with/without `--remote-debugging-port`, even with NO GL flags) reproducibly yields:

```
ERROR:ui/gl/init/gl_factory.cc:110] Requested GL implementation (gl=none,angle=none) not found in allowed implementations: [...]
ERROR:components/viz/service/main/viz_main_impl.cc:190] Exiting GPU process due to errors during initialization
```

The browser process carries the flags on its command line; the GPU process never receives them — `--use-gl`/`--use-angle` handoff is broken outside the real Wayland session (missing DBus / XAUTHORITY / display-socket session context). Browser stays alive, GPU process crash-loops, everything renders software.

Consequence: every flag combination looks equally broken from a shell → false conclusion. Only a Chrome launched from the real desktop session (app menu / `.desktop` / GUI) is authoritative. CDP queries (`chrome://gpu` via `--remote-debugging-port`) are affected the same way when the instance was shell-launched.

## Real verification — GPU process /proc

Browser process cmdline = flags PASSED. GPU process cmdline = flags USED. Check the GPU process:

```bash
for p in $(pgrep -f 'type=gpu-process'); do
  cl=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
  echo "PID $p: $(echo "$cl" | grep -oE -- '--use-gl=[a-z]+|--use-angle=[a-z]+')"
done
```

- `--use-gl=disabled` on the GPU process → software fallback (invalid flag or handoff failure)
- `--use-gl=angle` on the GPU process → GL backend actually handed off
- Note: `grep -oE` needs `--` before a pattern starting with `-` (otherwise "stray \ before -" warnings), or use `grep -oP '(?<=--)[a-z-]+'`

## Root cause in the user's case

`~/.config/chrome-flags.conf` contained `--use-angle=desktop` (invalid). Desktop-launched Chrome → GPU process forced `--use-gl=disabled` → every chrome://gpu feature "Software only / Disabled". Fix: remove the invalid backend; keep `--use-gl=angle` (+ optionally `--use-angle=opengl`).

## Launch chain reminder

`~/.local/share/applications/google-chrome.desktop` (Exec with env vars: `LIBVA_DRIVER_NAME=nvidia NVD_BACKEND=direct`) → `/usr/bin/google-chrome-stable` wrapper reads `~/.config/chrome-flags.conf` (`$CHROME_USER_FLAGS`) → `/opt/google/chrome/google-chrome`.
