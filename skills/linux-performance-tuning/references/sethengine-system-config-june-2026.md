# sethengine System Configuration (June 2026)

System reference from the June 2026 session. Capture if same user reconnects.

## Hardware
- CPU: Intel Core Ultra 7 265K (Arrow Lake, 20C/20T, no HT) — P-cores 0-7 (~5.4 GHz), E-cores 8-19 (~4.6 GHz)
- GPU: NVIDIA RTX 5060 Ti 16GB (GB206/Blackwell), driver 595.71.05, CUDA 13.2
- RAM: 64GB DDR5-6000 (4x16GB CP16G60C36U5B.M8D1) — running at 5200 (XMP not enabled in BIOS)
- Motherboard: Gigabyte Z890 AERO G, BIOS F17f (2025-07-09)
- Storage Kingston SA2000M8 1TB (Linux: /, /home, swap) + WD SN850X 2TB (Windows NTFS)
- Display: 3440x1440 ultrawide @ 165Hz (Gigabyte-branded)

## Software Stack
- Distro: Manjaro Linux, kernel 7.0.10-1-MANJARO PREEMPT_DYNAMIC
- Desktop: KDE Plasma 6.6.5, Wayland, KWin 6.6.5
- NVIDIA driver 595.71.05, CUDA 13.2
- LM Studio (AI inference), ComfyUI (image gen), Docker (overlay2), Steam+Proton
- Hermes Desktop + Hermes Agent, Chrome (Wayland, VA-API), OpenCode
- PipeWire 1.6.5, Easy Effects, Gamemode 1.8.2, MangoHud

## Boot Params (session 1 — pre-June 7 crash, preempt=voluntary, no CPU isolation)
```
transparent_hugepage=madvise tsx=on nvidia_drm.modeset=1
pcie_aspm.policy=performance intel_pstate=active sched_itmt_enabled=1
preempt=voluntary pci=pcie_bus_perf pcie_ports=native vdso=2
skew_tick=1 futex_waitv=1 intel_iommu=on,igfx_off iommu=pt
workqueue.power_efficient=false cpufreq.default_governor=performance
```

## Boot Params (session 2 — post-June 7 reboot, isolcpus + preempt=full)
```
isolcpus=domain,managed_irq,0-7 nohz_full=0-7 rcu_nocbs=0-7
transparent_hugepage=madvise tsx=on nvidia_drm.modeset=1
pcie_aspm.policy=performance intel_pstate=active sched_itmt_enabled=1
preempt=full pci=pcie_bus_perf pcie_ports=native vdso=2
skew_tick=1 futex_waitv=1 intel_iommu=on,igfx_off iommu=pt
udev.log_priority=3 workqueue.power_efficient=false
cpufreq.default_governor=performance modprobe.blacklist=iTCO_wdt
```

Key changes from session 1 → session 2:
- `preempt=voluntary` → `preempt=full` (allows kernel to preempt GPU compositor threads)
- Added `isolcpus=domain,managed_irq,0-7` — isolate P-cores 0-7 for gaming
- Added `nohz_full=0-7` — adaptive tickless on P-cores
- Added `rcu_nocbs=0-7` — RCU callbacks offloaded from P-cores
- Added `modprobe.blacklist=iTCO_wdt` — disable watchdog timer

**Known issue**: `isolcpus=domain,managed_irq,0-7` includes `managed_irq` which allows NVMe MSI-X queue completions to land on isolated P-cores. First 8 NVMe queues (both drives) land on CPUs 0-7. Recommended fix: drop `managed_irq` → `isolcpus=domain,0-7`.

## IRQ Pinning
Custom `pin-irqs-dynamic.service` — all IRQs on E-cores:
- E-cores 8-9: NVIDIA GPU (8 MSI-X vectors, all verified on CPUs 8-9)
- E-cores 10-11: USB xHCI (both controllers on CPUs 10-11)
- E-cores 12-19: NVMe, audio, WiFi, ethernet
- P-cores 0-7: reserved for game/foreground

**Verified IRQ affinity** (session 2, post-reboot):
- GPU: 8/8 vectors on housekeeping CPUs 8-9 ✓
- USB: 2/2 on CPU 10-11 ✓
- WiFi: 16/16 on CPU 12-19 ✓
- NVMe: 8/16 queues land on isolated CPUs 0-7 ⚠️ (see `managed_irq` issue above)
- Audio and other: all on housekeeping ✓

## Scheduler (current, needs fix)
- `sched_min_granularity_ns=750000` (too low — 0.75ms)
- `sched_wakeup_granularity_ns=1000000` (too low — 1ms)
- `sched_latency_ns=6000000` (aggressive — 6ms)
- **Recommended fix:** min=3000000, wakeup=4000000, latency=12000000

## Crash History (session 1, boot -1: May 31 → Jun 7)
- **Uptime**: 7 days 4 hours
- **End**: Abrupt at Jun 7 23:52:27 — no clean shutdown, no kernel panic in logs
- **Trigger**: Dota 2 crash at 23:45:50 — `free(): invalid pointer` → SIGSEGV (heap corruption)
- **After crash**: System ran ~6.5 more minutes, then locked up solid (likely GPU/compositor deadlock)
- **Recovery**: Forced reset → boot 0 with new kernel params
- **Prior Dota 2 crashes in same session**: 5 others, same `free(): invalid pointer` / `munmap_chunk(): invalid pointer` pattern — known Dota 2 Linux bug
- **Coredumps preserved from boot -1**: Dota 2 (multiple), Hermes desktop app, Wireplumber, EasyEffects
- **nvidia-powerd**: `ERROR! Running on an unsupported system (PCI device Id: 0x2d04)` — RTX 5060 Ti not in powerd whitelist, harmless

## SATA Controller in BIOS
- Z890 AERO G has SATA controller **disabled in BIOS by default** — not in lspci at all
- Fix: reboot → BIOS → Peripherals → SATA Configuration → Enabled

## Known Config Issues (addressed in sessions)
1. XMP disabled → RAM at 5200 instead of 6000 MT/s (fix: enable in BIOS)
2. thp-settings.service has typo ("madwise") — needs s/madwise/madvise/g
3. Ext4 errors on /home — schedule fsck
4. /home 94% full — clean up or migrate to WD SN850X
5. WiFi power_save was ON at runtime — fixed via modprobe options
6. irqbalance disabled by design (custom pin-irqs replaces it)
7. LIBVA_DRIVER_NAME conflict (nvidia vs nvidia_vulkan)
8. i915 in mkinitcpio MODULES but blacklisted — remove from MODULES
9. DXVK_ASYNC=1 in env AND dxvk.conf — remove from env, keep in dxvk.conf
10. `isolcpus=managed_irq` defeats NVMe isolation — 8 NVMe queues on isolated P-cores
