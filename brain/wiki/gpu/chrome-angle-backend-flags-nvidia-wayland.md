---
source_session: 20260801_020623_cb4276
date: 2026-08-01
category: gpu
tags: [chrome, nvidia, wayland, angle, vulkan, gpu-flags, chrome-flags-conf]
---

# Chrome ANGLE Backend Flags on NVIDIA Wayland

Chrome 149 on NVIDIA 610.43.03 + KDE Wayland: only ANGLE backends `opengl`, `opengles`, `vulkan` are allowed. `--use-angle=desktop` / `--use-gl=desktop` are invalid → GPU process forces `--use-gl=disabled` (software rendering). Vulkan is hard-blocked under Ozone Wayland (`'--ozone-platform=wayland' is not compatible with Vulkan`; crbug 848385/1469895). Native desktop GL (GLX) doesn't exist on Wayland. The only hardware path is ANGLE→OpenGL: `--use-gl=angle --use-angle=opengl` (or `gles`) — Chrome's Wayland default.

Flags live in `~/.config/chrome-flags.conf` (read by the google-chrome wrapper via `$CHROME_USER_FLAGS`).

**Verification:** `chrome://gpu` → Graphics Feature Status (Canvas/Compositing/WebGL "Hardware accelerated", not "Software only") plus the GPU process `/proc/<pid>/cmdline`.

**Pitfall:** launching Chrome from a non-graphical shell makes the GPU process receive no GL flags (`gl=none,angle=none`) — terminal tests are unreliable; validate from the real desktop session. Dawn `eglChooseConfig` warnings are WebGPU probes, not main-GL failures.

[[chrome-hw-video-accel-nvidia-wayland]] [[chrome-nvdec-xid31-input-latency]]
