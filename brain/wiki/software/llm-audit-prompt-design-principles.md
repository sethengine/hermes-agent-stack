---
source_session: "20260711_143618_f492c9"
date: 2026-07-11
category: software
related: [linux-latency-tuning, linux-performance-tuning, linux-system-audit-prompt]
---

# LLM Audit Prompt Design Principles

When designing system audit prompts for LLMs, describe **domains to investigate** not specific commands.

## Key insight (from iterative refinement)

Specific commands limit the LLM — it only checks what you explicitly listed. Instead, describe what the LLM should *discover*:

| Bad (command-first) | Good (domain-first) |
|---|---|
| `cat /proc/cpuinfo \| grep "model name"` | "Discover CPU model, topology, cores/threads, hybrid layout" |
| `cat /sys/module/usbhid/parameters/kbpoll` | "For every input device: USB bus path, HID polling interval, kernel overrides, hwdb quirks" |

## Design rules

1. Layer the audit (e.g., kernel cmdline → scheduler → IRQ → GPU → memory → I/O → input → audio → network → services → boot → sleep)
2. For each layer, describe **what to find** — let the LLM discover the commands
3. Every command block prefixed `## MANUAL EXECUTION` (prevents auto-apply)
4. Mandate web search per domain for current best practices
5. Output format: audit cmd → current value → target → fix → verify → persistence

[[linux-latency-tuning]] [[linux-performance-tuning]]
