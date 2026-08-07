---
source_session: "20260612_215142_27fb3c"
extracted_at: "2026-06-12T19:07:18Z"
category: "gpu"
tags: [lact, nvidia, segfault, gl, gtk4, gpu-monitoring]
---

# LACT GUI Segfault Fix (NVIDIA 595.71.05)

LACT GUI (v0.9.0-1) crashes with **SIGSEGV** immediately on launch under NVIDIA driver 595.71.05. The crash occurs in `libnvidia-glcore.so.595.71.05` at offset `0xcd7143` — the NVIDIA GL driver's context initialization path.

## Root Cause
GTK4/libadwaita creates an OpenGL context during rendering. The NVIDIA 595.71.05 driver segfaults in the GL worker thread spawned by this context init, not in LACT's own code. The crash is in the same driver family as [[nvidia-r595-driver-bugs-linux|Xid 31 MMU faults]].

## Fix
Run LACT GUI with threaded GL optimizations disabled:

```bash
__GL_THREADED_OPTIMIZATIONS=0 lact gui
```

## Permanent Setup
```bash
# In ~/.zshrc
export __GL_THREADED_OPTIMIZATIONS=0

# Desktop file override
mkdir -p ~/.local/share/applications
cp /usr/share/applications/io.github.ilya_zlobintsev.LACT.desktop ~/.local/share/applications/
sed -i 's|^Exec=lact gui|Exec=env __GL_THREADED_OPTIMIZATIONS=0 lact gui|' ~/.local/share/applications/io.github.ilya_zlobintsev.LACT.desktop
```

## LACT Architecture
- **`lactd`** — system daemon (runs as user service), manages GPU settings, persists config, survives GUI disconnect
- **`lact gui`** — GTK4 client, connects to daemon via `/run/lactd.sock`, can be stopped independently
