# Research Findings — 2026-07-12 Audit

**System:** Intel Core Ultra 7 265K (Arrow Lake) | RTX 5060 Ti (595.71.05) | KDE 6.6.5 Wayland | PipeWire 1.6.5

## Verified Findings (cross-referenced across 2+ sources)

### EEVDF Scheduler (kernel 7.0)
- Auto-prioritizes latency-sensitive tasks via lag-based virtual deadlines
- **No CFS tunables exist** (`sched_min_granularity_ns` etc. paths are gone)
- Arrow Lake hybrid (P/E core) handled natively via `cpu_capacity` — no manual tuning needed
- `sched_itmt_enabled=1` is designed for single-architecture Xeon, may be counterproductive on hybrid
- Source: kernel.org docs + Linux Magazine #301 + LWN.net refs

### NVIDIA 595.58.03+ Driver Fixes & Features (confirmed by 3 sources)
- `modeset=1` enabled by default (NVIDIA forums #362561, UbuntuHandbook, Phoronix)
- DRI3 v1.2 with DMA Fences (NVIDIA forums #362561, UbuntuHandbook)
- VK_EXT_present_timing — smooth frame pacing (NVIDIA forums #362561, UbuntuHandbook)
- VK_EXT_descriptor_heap — reduced CPU overhead (NVIDIA forums #362561, UbuntuHandbook)
- KWin Wayland display wake-up fix (Phoronix, UbuntuHandbook)
- X11 compositor blink regression fixed (from 580.119.02) (Phoronix, UbuntuHandbook)
- VRR HDMI flickering fix (UbuntuHandbook)
- Better VRAM→system memory fallback — prevents Wayland desktop freezes (UbuntuHandbook, Phoronix)
- GPU hang/Xid in Black Myth: Wukong fixed (NVIDIA forums #362561, UbuntuHandbook)
- HDR works without VK_HDR_LAYER or ENABLE_HDR_WSI (UbuntuHandbook, NVIDIA forums)
- Known: RTX 5090 Xid 109 CTX SWITCH TIMEOUT (not RTX 5060 Ti) — NVIDIA forums #362561

### Wayland Feature Limitations (confirmed — architectural, not fixable)
- Stereo rendering via GLX/EGL — not supported
- Implicit SLI Mosaic — not supported (explicit via VK_KHR_device_group)
- nvidia-settings display config — not available (power info still works)
- Features planned: mux switching, pixel shift, vGPU
- Source: NVIDIA Developer Forums #365749 (NVIDIA employee post)

### PipeWire 1.6.5
- WirePlumber 0.5.14 uses SPA-JSON syntax (not 0.4 Lua)
- Quantum 512 @ 48kHz = 10.67ms — stable with EasyEffects chain (15+ nodes including deepfilternet)
- Quantum 256 = 5.33ms — for gaming without effects chain
- `api.alsa.periods=3` creates ~32ms total ALSA buffer — can reduce to 2 for lower latency
- No xruns at quantum 512 with full EasyEffects chain on Arrow Lake 20-core

### GRUB Parameters — Reliability vs Latency Trade-offs
- `preempt=full` + `threadirqs`: best for desktop, no known stability issues
- `intel_idle.max_cstate=1`: prevents C-state exit jitter (up to 155µs on Arrow Lake C10)
- `processor.max_cstate=1`: **redundant** with intel_idle equivalent — same effect at ACPI level
- `sched_itmt_enabled=1`: designed for Xeon, undocumented on hybrid — remove on Arrow Lake
- Arrow Lake vulnerability status: 14/18 "Not affected" — remaining 4 (Spectre v1/v2, SSB, Vmscape) have minimal impact. `mitigations=off` yields 1-3% gain at most.

### IRQ Layout — Verified Optimal
- GPU IRQs: CPU8 (1.0M) and CPU10 (1.4M) — likely E-cores, leaving P-cores free for game threads
- USB xhci_hcd: CPU13 (470K) — isolated from GPU IRQs ✅
- NVMe 14 queues: spread across 8+ cores ✅
- iwlwifi 14 queues: spread across 8+ cores ✅
- irqbalance inactive (correct for manual tuning)

### Storage Tuning
- `none` I/O scheduler is correct for NVMe (hardware does its own scheduling)
- NVMe APST can cause 50µs-10ms I/O stalls on wake — `default_ps_max_latency_us=0` disables it
- Ext4 above 90% fullness degrades performance significantly (allocation fragmentation)
