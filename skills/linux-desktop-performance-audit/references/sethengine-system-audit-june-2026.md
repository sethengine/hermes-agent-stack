# System Audit: sethengine-desktop — June 2026

This is a worked example of a full `linux-desktop-performance-audit` on a real system. Use it as a template when auditing similar setups.

## System Profile

| Component | Detail |
|---|---|
| **CPU** | Intel Core Ultra 7 265K (Arrow Lake) — 20 cores (8P + 12E), no HT |
| **GPU** | NVIDIA GeForce RTX 5060 Ti (GB206 / Blackwell) — 16 GB VRAM |
| **RAM** | 62 GiB (64 GiB installed) — DDR5-6000 rated, running at 5200 (XMP disabled) |
| **Swap** | 15.6 GiB on NVMe — 3.3 GiB used |
| **Boot drive** | Kingston SA2000M8 1 TB (nvme1n1) — / and /home on ext4, noatime |
| **Storage** | WD_BLACK SN850X 2 TB (nvme0n1) — all NTFS (Windows) |
| **Kernel** | 7.0.10-1-MANJARO — PREEMPT_DYNAMIC, preempt=voluntary |
| **NVIDIA Driver** | 595.71.05 — CUDA 13.2 |
| **Display** | KDE Plasma 6.6.5 / Wayland — 3440x1440 ultrawide |
| **GPU clocks (idle)** | 1687 MHz core, 13801 MHz memory |
| **Max clocks** | 3090 MHz core |
| **Power limit** | 184 W (default 180 W, max 198 W) |
| **Motherboard** | Gigabyte Z890 AERO G (BIOS F17f, July 2025) |
| **Audio** | ALSA default through NVIDIA HDMI (card 0), not ALC1220 (card 1) |
| **Network** | WiFi 6 via iwlwifi (Intel AX411), power_save=ON |
| **Notable software** | ComfyUI (111GB models), LM Studio, Steam/Proton, Docker, Hermes Agent, OpenCode, Easy Effects, Gamemode, MangoHud |

## Research Context (from last30days v3.3.1 — 8 passes)

### Passes conducted:
1. **Arrow Lake / Core Ultra 265K tuning** — No specific tuning guides found; generic Intel roadmap news.
2. **NVIDIA Wayland + KDE Plasma** — KDE 6.8 drops X11 Oct 2026; Wayland future confirmed. Community skeptical of NVIDIA Linux promises.
3. **Gigabyte Z890 BIOS / DDR5** — D5 Single Boost announced; Aero G preferred for Intel NICs on r/homelab.
4. **Manjaro kernel tuning** — No specific tuning threads found.
5. **Proton + NVIDIA Wayland gaming** — r/linux_gaming rant (1592pts) confirmed NTFS→ext4 fixes major Proton issues. Community consensus: use ext4 for game libraries.
6. **NTFS vs ext4 gaming** — u/Financial-Gap-6767: "swapped my game from ntfs drive to ext4... everything just work" (127 upvotes).
7. **GSP firmware (Blackwell)** — No Blackwell-specific GSP discussion found.
8. **ComfyUI + NVIDIA optimization** — Only a bug report thread found.

### Key research signals:
> **r/linux_gaming (1,592 pts, 405 cmt):** Jensen Huang teased "exciting things on Linux." Top comment (2,290 upvotes from u/WesRabbit): *"AI. Nothing relevant that doesn't involve AI has come from Jensen Huang or NVIDIA in the last few years."*
> The community is deeply skeptical of NVIDIA Linux promises. No dedicated Wayland+NVIDIA tweak guides surfaced in the 30-day window.

## Audit Findings

### Already Optimal (acknowledged)

- `noatime` on / and /home — correct
- `none` NVMe scheduler — correct
- `fstrim.timer` active — correct
- `nvidia_drm.modeset=1` + `fbdev=1` — correct
- `NVreg_EnableResizableBar=1` — correct for RTX 5000 series
- `NVreg_UsePageAttributeTable=1` — correct
- `PowerMizerLevel=0x2` (max performance) — correct
- `LatencyPolicy=LatencyLow` in kwinrc — correct
- `VrrPolicy=Always` — correct for VRR monitor
- `AllowTearing=true` — correct for gaming
- `UnredirectFullscreen=true` — correct
- `__GL_SYNC_TO_VBLANK=0` — correct for VRR + tearing
- `__GL_MaxFramesAllowed=1` — correct (low latency)
- `__GL_VRR_ALLOWED=1` — correct
- `__GL_SHADER_DISK_CACHE_SIZE=10GB` — generous but fine
- `PROTON_ENABLE_ESYNC=1`, `PROTON_ENABLE_FSYNC=1` — correct
- `cpufreq.default_governor=performance` — correct intent (intel_pstate "powersave" is naming quirk; EPP=performance confirms real mode)
- Firefox running MOZ_ENABLE_WAYLAND=1 natively — correct
- `transparent_hugepage=madvise` — correct (not "always")
- VM swappiness=5 — correct for low swap pressure
- NVIDIA persistence daemon active — correct
- IOMMU in passthrough mode — correct for GPU

### Tier 1 — Real bugs and critical issues

| # | Problem | Source | Fix |
|---|---|---|---|
| 1 | **XMP disabled** — 4x16GB DDR5-6000 at 5200 MT/s (-15% bandwidth) | dmidecode | Enable XMP Profile 1 in BIOS |
| 2 | **thp-settings.service typo** — writes "madwise" instead of "madvise" | systemctl cat | `sed -i 's/madwise/madvise/g'` in service file |
| 3 | **/home ext4 errors** — fsck found corruption | tune2fs + fsck | `sudo tune2fs -C 65535 /dev/nvme1n1p1 && reboot` |
| 4 | **/home 94% full** (660GB/737GB) — ext4 degrades past 90% | df -h | Free 50GB+ or move ComfyUI (111GB) to WD |
| 5 | **WiFi power_save=ON** — 10-200ms network jitter | iw dev | `iw dev wlp131s0f0 set power_save off` + systemd service |
| 6 | **irqbalance disabled** — 6% CPU pressure, NVIDIA IRQs on CPU0/2 only | systemctl + /proc/interrupts | Enable irqbalance, disable pin-irqs-dynamic |
| 7 | **LIBVA_DRIVER_NAME conflict** — `nvidia` vs `nvidia_vulkan` across env files | env source cross-ref | Align to `nvidia_vulkan` in environment.d |

### Tier 2 — Performance-impacting

| # | Problem | Source | Fix |
|---|---|---|---|
| 8 | CPU mitigations active (2-8% perf loss) | /proc/cmdline | Add `mitigations=off` to GRUB |
| 9 | C-states allow C3 (1048μs wake latency) | cpuidle latency | Add `intel_idle.max_cstate=2` to GRUB |
| 10 | GSP firmware was disabled (NVreg_EnableGpuFirmware=0) | modprobe.d | Changed to =1 (firmware exists at /lib/firmware/nvidia/gb206/) |
| 11 | Games may be on NTFS (WD SN850X) | lsblk + **research** | Move Steam library to ext4 on Kingston |
| 12 | No zram (swap on disk) | zramctl + swapon | Install zram-generator |
| 13 | NVMe read-ahead too low (128/512 KB) | sysfs | udev rule to set 2048 KB |
| 14 | preempt=voluntary (already in grub as full, needs reboot) | grub vs cmdline mismatch | `sudo update-grub && sudo reboot` |
| 15 | No user-scope memlock (affects CUDA/LM Studio) | limits.d | Add limits.d/99-cuda-memlock.conf |

### Tier 3 — Config cleanup

| # | Problem | Source | Fix |
|---|---|---|---|
| 16 | i915 in mkinitcpio MODULES but blacklisted | mkinitcpio.conf vs modprobe.d | Remove from MODULES |
| 17 | i915 options in arrow-lake-ai.conf (targets blacklisted module) | modprobe.d cross-ref | Comment out the i915 option line |
| 18 | DXVK_ASYNC in env AND dxvk.conf (obsolete) | env + dxvk.conf | Remove from both env files |
| 19 | usbhid-latency.conf overridden by boot param | modprobe.d vs cmdline | Remove redundant file |
| 20 | Redundant nvidia-performance autostart | autostart vs modprobe | Remove desktop entry |
| 21 | ALSA default → NVIDIA HDMI, not ALC1220 | asoundrc + /proc/asound/cards | Switch card 0→1 in ~/.asoundrc |
| 22 | KWIN_TRIPLE_BUFFER=0 (KDE5 relic, does nothing on KDE6) | .profile | Remove stale var |
| 23 | Duplicate env vars (__GL_VRR_ALLOWED) | env cross-ref | Clean one source |
| 24 | xfs/jfs/thunderbolt modules loaded unused | lsmod | Blacklist in modprobe.d |
| 25 | ftrace_enabled=1 (tiny overhead) | /proc/sys/kernel | Set to 0 in sysctl.d |
| 26 | debugfs/tracefs mounted | mount | Add to fstab with `none` |

### Tier 4 — Nice-to-have

| # | Improvement |
|---|---|
| 27 | GPU power limit 198W (+14W headroom, ~3-5% perf) |
| 28 | Tighter VM dirty ratios (10/3 instead of 15/5) |
| 29 | PipeWire quantum=256 (5.3ms instead of 21ms) |
| 30 | Disable KDE blur effect (GPU overhead on NVIDIA Wayland) |
| 31 | Enable NVPRESENT smooth motion |
| 32 | Install tuned + profile latency-performance |
| 33 | Install psd (browser profiles on tmpfs) |
| 34 | Compiler flags: -march=native -O3 in /etc/makepkg.conf |
| 35 | Chrome: switch from ANGLE to EGL |
| 36 | Lower watermark_boost_factor |

## Env Var Source Map

| Var | /etc/environment | environment.d/*.conf | ~/.profile | Status |
|---|---|---|---|---|
| DXVK_ASYNC=1 | ✓ | — | ✓ | Obsolete |
| __GL_SYNC_TO_VBLANK=0 | ✓ | — | — | Good |
| __GL_VRR_ALLOWED=1 | ✓ | ✓ (99-nvidia.conf) | — | Duplicate |
| __GL_YIELD=USLEEP | — | ✓ (99-nvidia.conf) | — | Good |
| __GL_MaxFramesAllowed=1 | ✓ | — | — | Good |
| __GL_SHADER_DISK_CACHE_SIZE=10GB | — | ✓ (99-nvidia.conf) | — | Good |
| __GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1 | comments only | ✓ (99-nvidia.conf) | ✓ | Good |
| DXVK_FRAME_RATE=0 | ✓ | — | — | Good |
| PROTON_ENABLE_ESYNC=1 | ✓ | — | — | Good |
| PROTON_ENABLE_FSYNC=1 | ✓ | — | — | Good |
| PROTON_ENABLE_NVAPI=1 | ✓ | — | ✓ | Duplicate |
| LIBVA_DRIVER_NAME | — | nvidia (99-chrome-vaapi) | nvidia_vulkan | CONFLICT |
| NVD_BACKEND=direct | — | ✓ (99-nvidia.conf) | ✓ | Good |
| NVPRESENT_ENABLE_SMOOTH_MOTION=1 | — | ✓ (99-nvidia.conf) | — | Good |
| GBM_BACKEND=nvidia-drm | — | ✓ (99-nvidia.conf) | — | Good |
| KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1 | ✓ | — | — | Good |
| KWIN_DRM_ALLOW_TEARING=1 | ✓ | ✓ (99-kwin-latency) | — | Duplicate |
| KWIN_TRIPLE_BUFFER=0 | — | — | ✓ | KDE5 relic (no-op) |

## Boot Parameter Reference

From `/etc/default/grub`:
```
transparent_hugepage=madvise tsx=on usbhid.mousepoll=1
nvidia_drm.modeset=1 usbhid.kbpoll=1 pcie_aspm.policy=performance
intel_pstate=active sched_itmt_enabled=1 preempt=voluntary
pci=pcie_bus_perf pcie_ports=native vdso=2 skew_tick=1 futex_waitv=1
modprobe.blacklist=iTCO_wdt intel_iommu=on,igfx_off iommu=pt
udev.log_priority=3 workqueue.power_efficient=false
cpufreq.default_governor=performance
```

Note: Running kernel had `transparent_hugepage=madvise` 3x (grub duplication bug) and `preempt=voluntary` while grub file had `preempt=full` (unapplied change).

## NVIDIA Modprobe Config

```nvidia.conf
blacklist nouveau
options nvidia \
  NVreg_EnableMSI=1 \
  NVreg_PreserveVideoMemoryAllocations=1 \
  NVreg_TemporaryFilePath=/var/tmp \
  NVreg_EnableGpuFirmware=0 \           # ← FIXED to =1 in session
  NVreg_DynamicPowerManagement=0x02 \
  NVreg_UsePageAttributeTable=1 \
  NVreg_EnableResizableBar=1 \
  NVreg_RegistryDwords="PerfLevelSrc=0x2222;PowerMizerLevel=0x2;...RMIntrLockingMode=1;RMUseSwDithering=1"
options nvidia_drm modeset=1 fbdev=1
```

## Cross-Config Conflicts Found

1. **Boot param duplication**: `transparent_hugepage=madvise` appeared 3x in /proc/cmdline (grub-duplicated).
2. **Grub drift**: grub file says `preempt=full`, running kernel says `preempt=voluntary`.
3. **Module conflict**: i915 in mkinitcpio MODULES but blacklisted in modprobe.d.
4. **IRQ conflict**: pin-irqs-dynamic.service (custom script) and irqbalance.service both exist as options.
5. **Env spreading**: `__GL_VRR_ALLOWED=1` in both /etc/environment and environment.d; `PROTON_ENABLE_NVAPI=1` in both /etc/environment and ~/.profile.
6. **GPU perf duplication**: modprobe.conf Forces PowerMizerLevel, AND autostart runs nvidia-settings to do the same thing.
7. **LibVA driver conflict**: `nvidia` (legacy) vs `nvidia_vulkan` (modern) across env files.
8. **i915 option dead config**: arrow-lake-ai.conf has `options i915 enable_guc=2` but i915 is blacklisted.
9. **KDE5 relic**: `KWIN_TRIPLE_BUFFER=0` in `.profile` does nothing on KDE6.
10. **ALSA routing**: Default points to NVIDIA HDMI (card 0) instead of motherboard ALC1220 (card 1).

## Round-Based Discovery Pattern (Methodology Note)

This audit was conducted in 4 rounds, each triggered by the user asking "find more":
1. **Rounds 1-4** (HW, kernel, GPU, P-State) — 6 findings
2. **Rounds 5-7** (storage, memory, services) — 9 more findings
3. **Rounds 8-10** (audio, network, desktop effects) — 8 more findings
4. **Cross-config conflicts** + firmware + XMP — 8 more findings + 8 research passes

The user's escalation signal was "a more a moore" (find more, go deeper, don't stop). Each round covered a new layer rather than re-iterating the same one.

## Context Switch Analysis

### Live Metrics (active gaming session)

- **Total CS since boot (6.2 days):** 14.5+ billion
- **Current rate:** 231,385 CS/s (measured during active Risk of Rain 2 + Chrome + VLC)

### Top CS Consumers (Risk of Rain 2 via Proton)

| Process | Voluntary CS | Involuntary CS | Total | Notes |
|---|---|---|---|---|
| wineserver | 17,640,095 | 30,213 | 17,670,308 | Expected -- every Windows API call |
| xalia.exe | 9,229,168 | 83,529 | 9,312,697 | Xbox Game Bar integration -- OPTIONAL |
| Risk of Rain 2 | 8,927,038 | 324,005 | 9,251,043 | 324K NV = forced preemption by GPU IRQs |

### Root Cause: GPU IRQ Preemption

The 324,005 involuntary CS for Risk of Rain 2 is caused by **GPU IRQs preempting the game thread**, NOT the scheduler.

NVIDIA IRQ distribution:
```
IRQ 146 (nvidia): 73,575,569 on CPU 0  <- main GPU interrupt
IRQ 148 (nvidia): 112,870,681 on CPU 2 <- second GPU interrupt
```

The game was running on P-cores 0-7 (where the scheduler naturally placed it), but **P-cores 0 and 2 handle 186M GPU interrupts**. When the game's main thread ran on CPU 0 or 2, every GPU interrupt preempted it.

### Scheduler Contribution

The sysctl settings amplified CS system-wide but were NOT the main cause of game involuntary CS:
- `sched_min_granularity_ns=750000` (0.75ms vs default 3ms) -> 4x more preemptions system-wide
- These settings caused 231K CS/s across the system but only ~90 CS/s of the game's 324K involuntary CS.

### Fix Applied (recommended)

1. **Spread NVIDIA IRQs across P-cores 1-7** (not just 0-5) to reduce per-core interrupt load
2. **Pin game to P-cores 6-7** (no NVIDIA IRQs) via gamemode: `[cpu] cores=6-7 pin_cores=yes`
3. **Restore scheduler values** for gaming: min_granularity=3ms, wakeup=4ms, latency=12ms
4. **Enable gamemoderun %command%** in Steam launch options (gamemode installed but inactive)
5. **Remove xalia.exe** (Xbox Game Bar) overhead if not needed

## IRQ Pinning Strategy (Custom pin-irqs-dynamic)

The user has a custom IRQ pinning script that distributes interrupts by CPU type:
- **P-cores (0-7, 5.4 GHz):** NVIDIA GPU (spread across 0-5) + USB xHCI (6-7)
- **E-cores (8-19, 4.6 GHz):** Audio (snd_hda_intel -> 8-9), NVMe (8-19), WiFi (iwlwifi -> 8-19)

This is the correct strategy for hybrid CPUs -- GPU IRQs need P-core latency, background I/O can use E-cores.

The one improvement: NVIDIA IRQs should spread across P-cores 1-7 rather than 0-5 to avoid concentrating 186M interrupts on just two cores.

## Network Stack Notes

- **WiFi:** Intel AX411 on wlp131s0f0, 5220 MHz 80MHz channel
- **Link:** 390 Mbps TX / 351 Mbps RX (WiFi 6 at -63 dBm signal)
- **Latency to 1.1.1.1:** 16.7-17.2ms (expected for WiFi)
- **Ethernet ports (unused):** Dual Intel I225-V 2.5GbE on enp129s0/enp130s0
- **BBR congestion control:** Active
- **MTU:** 1420
- **Qdisc:** noqueue (0.5ms jitter -- fine)
- **tcp_notsent_lowat:** UINT_MAX (disabled)
- **IRQ distribution:** WiFi IRQs on E-cores 8-19 (correct)
