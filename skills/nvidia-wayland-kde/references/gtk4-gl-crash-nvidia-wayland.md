# GTK4/libadwaita GL Renderer Crash on NVIDIA Wayland

## Symptom

GTK4/libadwaita GUI apps crash with SIGSEGV (segfault) in `libnvidia-glcore.so` on NVIDIA Wayland. The daemon log shows:

```
PID: 61950 (lact)
Signal: 11 (SEGV)
Command Line: /usr/bin/lact gui
Executable: /usr/bin/lact
```

The crashing thread's stack trace is inside `libnvidia-glcore.so` — not in the app's own code:

```
Stack trace of thread 62025:
#0  0x00007f83bd6d7143 n/a (libnvidia-glcore.so.595.71.05 + 0xcd7143)
#1  0x00007f83bd3f5a74 n/a (libnvidia-glcore.so.595.71.05 + 0x9f5a74)
```

Multiple threads simultaneously stuck in the NVIDIA driver:
- `libnvidia-glcore.so` (GL core — the crashing thread)
- `libnvidia-present.so` (presentation/display — threads blocked on `pthread_cond_wait`, `pthread_cond_timedwait`, `__nanosleep`)
- `libcuda.so.1` (CUDA — threads polling)

The main GTK thread is fine (running `g_application_run`). The crash is in a GPU worker thread spawned internally by the NVIDIA GL library.

## Root Cause

GTK4's default GL scene-graph renderer (historically called "ngl", now renamed back to "gl" in GTK 4.14+) creates an OpenGL context via `libnvidia-glcore.so`. On NVIDIA driver 595.71.05 with Wayland, this GL context initialization or rendering triggers a segfault inside the driver. This is an NVIDIA driver bug, not a bug in the affected app.

The crash has been reported across multiple NVIDIA driver versions going back years (535.x, 545.x, 590.x, 595.x) — it's a recurring class of bug in NVIDIA's OpenGL core library.

## Affected Applications

Any GTK4/libadwaita app that initializes an OpenGL context on NVIDIA Wayland can trigger this:

- **LACT** (Linux GPU Configuration Tool) — the primary case documented here
- GNOME Control Center (`gnome-control-center`)
- Other libadwaita-based GTK4 applications

## Fix (Two Confirmed Approaches)

### Approach A — Force Vulkan Renderer (preferred)

Set `GSK_RENDERER=vulkan` before launching the affected app:

```bash
# One-shot
GSK_RENDERER=vulkan lact gui

# Permanent (add to ~/.zshrc)
export GSK_RENDERER=vulkan
```

This forces GTK4 to use its Vulkan scene-graph renderer instead of the OpenGL renderer. The Vulkan renderer uses a different code path through the NVIDIA driver (`libnvidia-vulkan-producer.so` and Vulkan ICD) which does **not** trigger this segfault.

**Confirmed**: Verified working with 22+ seconds of uptime (crashes without it were instant).

### Approach B — Disable GL Threaded Optimizations (alternative)

The crash occurs in a GPU worker thread spawned internally by `libnvidia-glcore.so`. Disabling these GL worker threads prevents the crash at the source:

```bash
# One-shot
__GL_THREADED_OPTIMIZATIONS=0 lact gui

# Permanent (add to ~/.zshrc)
export __GL_THREADED_OPTIMIZATIONS=0
```

This environment variable tells the NVIDIA GL driver not to spawn worker threads for GL command processing. The crash in `libnvidia-glcore.so + 0xcd7143` happens in one of those worker threads. Trade-off: potentially lower GL performance, but for a monitoring tool like LACT this is irrelevant.

**Confirmed**: Verified working with 15+ seconds of uptime (same instant-crash baseline).

This same workaround has been documented by Arch users for SIGBUS/SIGSEGV in games (e.g. `__GL_THREADED_OPTIMIZATIONS=0` fixed game crashes on NVIDIA 565.x drivers).

### Combination (most robust)

Apply both for maximum robustness:

```bash
GSK_RENDERER=vulkan __GL_THREADED_OPTIMIZATIONS=0 lact gui
```

### Fallback — X11 Backend

If neither workaround helps:

```bash
GDK_BACKEND=x11 lact gui
```

This runs the app under XWayland, which uses a completely different GLX code path through the NVIDIA driver, avoiding the Wayland OpenGL crash entirely.

### Verification

After setting either variable, the app starts, connects to the daemon, and renders normally without crashing:

```
2026-06-12T18:55:47.016060Z  INFO i18n_embed::requester: Current Locale: ...
2026-06-12T18:55:47.273183Z  INFO lact_client::connection::unix: connecting to service at "/run/lactd.sock"
```

## Desktop Entry Override

To make the fix permanent for LACT's desktop launcher:

```bash
mkdir -p ~/.local/share/applications
cp /usr/share/applications/io.github.ilya_zlobintsev.LACT.desktop ~/.local/share/applications/
# Then edit the Exec= line:
sed -i 's|^Exec=lact gui|Exec=env GSK_RENDERER=vulkan __GL_THREADED_OPTIMIZATIONS=0 lact gui|' ~/.local/share/applications/io.github.ilya_zlobintsev.LACT.desktop
```

## Reference Info

### System Details (from the documented case)

| Item | Value |
|------|-------|
| Distribution | Manjaro Linux |
| Kernel | 7.0.10-1-MANJARO |
| Desktop | KDE Plasma 6 (Wayland) |
| GPU | RTX 5060 Ti |
| NVIDIA Driver | 595.71.05 |
| LACT version | 0.9.0-1 |
| GTK4 version | 4.22.4 |

### Core Dump Info

The crash produces a ~20 MB core dump stored by systemd-coredump:

```
Storage: /var/lib/systemd/coredump/core.lact.1000.245f9784357b45b0943c019c817f1402.61950.1781290264000000.zst
```

Clean up with: `sudo rm /path/to/core.zst`

### Diagnostic Commands

```bash
# Check for recent LACT crashes
coredumpctl list --since "5 minutes ago" 2>/dev/null | grep lact

# Get crash details
coredumpctl info <PID> 2>/dev/null | head -40

# Check daemon logs
journalctl -u lactd --no-hostname -n 20

# Check what version is installed
pacman -Qi lact 2>/dev/null | grep -E "^(Name|Version)"
```
