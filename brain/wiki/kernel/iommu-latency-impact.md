---
source: session 20260609_195359_ab296b (Keyboard Input Latency Investigation)
date: 2026-06-09
category: kernel/
---

# IOMMU Latency Impact

IOMMU (Input/Output Memory Management Unit) acts as an MMU for devices — translating I/O virtual addresses to physical RAM addresses and providing device isolation via DMA remapping.

## Latency Implications

- Passing `intel_iommu=on,igfx_off iommu=pt` on the kernel cmdline adds DMA translation overhead to every GPU buffer exchange, even in pass-through mode.
- The `igfx_off` variant disables IOMMU for the integrated GPU only.
- For gaming/low-latency desktops, Intel IOMMU can add measurable latency to GPU operations.

## Trade-off

- **Without IOMMU**: lower latency, but no DMA isolation protection against malicious/errant devices.
- **With IOMMU**: security isolation (prevents device DMA attacks), at the cost of some latency.

See also: [[irq-pinning-usb-to-pcore]]
