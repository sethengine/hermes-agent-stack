---
title: USB Input Interrupt Priority Analysis
category: kernel
tags: [linux, irq, usb, latency, preemption, realtime]
source_session: 20260606_211351_5d5f13
created: 2026-07-29
related: [[linux-kernel-parameters]], [[irq-affinity-tuning]], [[preemption-models]]
---

# USB Input Interrupt Priority Analysis

Read-only analysis of USB IRQ priority on a Linux desktop (Manjaro, Intel 800 Series PCH xHCI controller, IRQ 138 pinned to CPU7). The system used [[linux-kernel-parameters|`preempt=voluntary`]] (not full preemption) and [[irq-threading|hardirq context]] (IRQ threading off). USB polling was already at 1ms (`usbhid.mousepoll=1`, `usbhid.kbpoll=1`). CPU7 also handled RTC (8), PCIe PME (126), and NVMe (161) IRQs.

## Key Findings

- **Preemption model**: `voluntary` (dynamic, selectable at boot via `CONFIG_PREEMPT_DYNAMIC=y`)
- **IRQ threading**: Off — all IRQs run in hardirq context, no RT priority possible
- **RT throttling**: Default 95/100ms (`/proc/sys/kernel/sched_rt_runtime_us`)
- **USB devices**: Keyboard and mouse on Bus 003 (PCH xHCI)

## Mitigation Approaches (ranked)

1. **`threadirqs` + `preempt=full`** — Most impactful. Threaded IRQs expose PIDs (`irq/138-xhci_hcd`) that can be given `chrt -f 99` (SCHED_FIFO). `preempt=full` lowers scheduling latency everywhere.
2. **`threadirqs` only** — Same chrt capability without full preemption overhead.
3. **Repin IRQ 138 to a quieter CPU** — CPUs 12–15 had no pinned IRQs. Zero-risk, no-reboot change via `/proc/irq/138/smp_affinity`.
4. **Disable RT throttling** (`sched_rt_runtime_us=-1`) — Risk of system lock if a FIFO-99 thread runs away.

No changes were applied — the session was purely investigative. See [[irq-affinity-tuning]] for repinning and [[preemption-models]] for kernel preemption options.
