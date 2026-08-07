---
source_session: 20260608_224916_653103
date: 2026-06-08
category: gpu
tags: [nvidia, chrome, nvdec, xid, latency, input-lag]
---

# Chrome NVDEC0 MMU Faults Causing Input Latency

Chrome's hardware video decoder (NVDEC0) can trigger NVIDIA GPU MMU page faults (Xid 31) on RTX 5060 Ti / Blackwell architecture. These faults block KWin compositing mid-frame, causing perceived mouse input lag.

## Symptoms

- Xid 31 faults logged every 5–15 minutes: `ENGINE NVDEC0 HUBCLIENT_NVDEC0 faulted @ ... FAULT_PDE ACCESS_TYPE_VIRT_WRITE`
- Rescheduling IPI storms on specific CPU cores
- KWin compositor stalls during fault handling

## Mitigations

1. **`--disable-accelerated-video-decode`** Chrome flag — disables HW video decode entirely (most effective)
2. **`RMNvDecSurfacesPerContext=16`** — NVIDIA RM registry key limiting NVDEC surface allocation. Set via kernel module parameter: `NVreg_RegistryDwords=RMNvDecSurfacesPerContext=16`. Default on Blackwell is 32–64 surfaces; reducing caps decode throughput but may reduce VA space pressure.

[[chrome-nvidia-wayland-latency]] [[nvidia-xid-31]] [[chrome-angle-nvidia-wayland]]
