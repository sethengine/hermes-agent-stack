---
name: system-spec
description: >-
  Full hardware + software specification for sethengine's workstation.
  Load this skill whenever system details are relevant — debugging,
  gaming advice, performance tuning, driver questions, kernel config.
  Rewrite this skill's spec section when any component changes.
tags:
  - system-spec
  - hardware
  - software
  - linux
  - gaming
  - nvidia
  - manjaro
---

# System Specification — sethengine-desktop

> **Last verified:** 2026-07-12  
> **Rewrite trigger:** any HW/SW change (new GPU, RAM, storage, OS upgrade, kernel change, driver update, monitor change)

---

## 🖥 System Overview

| Field | Value |
|-------|-------|
| Hostname | `sethengine-desktop` |
| OS | Manjaro Linux (rolling, Arch-based) |
| Kernel | `7.0.10-1-MANJARO` — PREEMPT_DYNAMIC |
| Desktop | KDE Plasma 6.26.0 (kded6) |
| Display Server | Wayland (via SDDM) |
| Session Type | `wayland` |

---

## 🧠 Motherboard / BIOS

| Field | Value |
|-------|-------|
| Manufacturer | Gigabyte Technology Co., Ltd. |
| Board | Z890 AERO G (rev x.x) |
| BIOS Vendor | American Megatrends International, LLC. |
| BIOS Version | F21 (2026-06-11) |

---

## ⚡ CPU

| Field | Value |
|-------|-------|
| Model | Intel Core Ultra 7 265K (Arrow Lake) |
| Cores / Threads | 20C / 20T (1 thread/core) |
| Base / Max Freq | 800 MHz / 5.50 GHz |
| L1d Cache | 704 KiB (18 instances) |
| L1i Cache | 1.1 MiB (18 instances) |
| L2 Cache | 36 MiB (11 instances) |
| L3 Cache | 30 MiB (1 instance) |
| Socket(s) | 1 |
| NUMA Nodes | 1 (CPU 0-19) |
| Virtualization | VT-x |
| Vulnerability L1TF | Not affected |

---

## 🎮 GPU

| Field | Value |
|-------|-------|
| Model | NVIDIA GeForce RTX 5060 Ti (GB206) |
| Driver | NVIDIA 595.71.05 (open kernel module) |
| VRAM | 16311 MiB (~16 GB GDDR7) |
| CUDA Version | 13.2 |
| NVCC | V13.2.78 |
| Bus | PCIe 4.0 x16 @ 02:00.0 |
| Power Limit | 184 W |
| Current Power | 30 W (idle, P1 state) |
| Temp | 40°C (idle, fan 34%) |
| VBIOS | — |
| Persistence Mode | On |

### Active GPU Processes (SMI)
- kwin_wayland (152 MiB)
- Xwayland (2 MiB)
- plasmashell (316 MiB)
- Hermes Desktop (177 MiB)
- Alacritty (57 MiB + 17 MiB)
- Zed Editor (485 MiB)
- EasyEffects (48 MiB)
- Steam (4 MiB + 34 MiB)

---

## 🧮 Memory

| Field | Value |
|-------|-------|
| Total | 64 GiB (4 × 16 GiB DDR5-5600) |
| Modules | CP16G60C36U5B.M8D1 |
| Speed | 5600 MT/s (configured) |
| Voltage | 1.25 V |
| Max Capacity | 128 GiB (board limit) |
| MemTotal (kernel) | ~62.5 GiB (~65.5 GB) |
| HugePages | 2048 × 2 MB (pre-allocated) |

---

## 💾 Storage

### NVMe Drives

| Device | Model | Size | Firmware | Health |
|--------|-------|------|----------|--------|
| `nvme0n1` | WD_BLACK SN850X 2000GB | 1.8 TiB | 620361WD | 0% used, 39°C |
| `nvme1n1` | KINGSTON SA2000M81000G | 931.5 GiB | S5Z42105 | 9% used, 34°C |

### Partitions
- **Root**: `/dev/nvme1n1p4` on `/` — 85 GiB total, 39 GiB used (49%)
- **Swap**: `/dev/nvme1n1p2` — 15.6 GiB (1.1 MiB used)

---

## 🖥 Display

| Field | Value |
|-------|-------|
| Monitor | HP X34 (ultrawide) |
| Resolution | 3440×1440 @ 165 Hz (native) |
| Connection | DisplayPort (DP-3) |
| VRR | Automatic |
| HDR | Disabled |
| EDID Override | `drm.edid_firmware=DP-3:edid/hp-x34.bin` |

---

## 🔊 Audio

| Field | Value |
|-------|-------|
| Server | PipeWire 1.6.5 (PulseAudio compat) |
| Default Sink | `alc1220-analog-sink` (ALC1220, hw:1) |
| Format | float32le 2ch 48000Hz |
| Resampler | soxr-vhq |
| Period Size | 512 |
| Amplifier | Douk Audio (external) |
| Headphones | Sony WH-1000XM3 (powered ON) |
| DSP | EasyEffects — Bass → Exciter → EQ(8-11k cut) → Limiter |
| ASound Cards | 0: HDA NVidia (GB206) · 1: HDA Intel PCH (ALC1220) |
| Config Repo | [github.com/sethengine/alc1220-audio-config](https://github.com/sethengine/alc1220-audio-config) |

---

## ⌨️ Input Devices

| Device | Vendor:Product | Notes |
|--------|---------------|-------|
| Corsair Katar Pro XT | `1b1c:1bac` | Gaming mouse, keyd-remapped |
| BY Tech Thor 230 | `331a:5020` | Keyboard, keyd-remapped |

Both have `usbhid.quirks` in kernel cmdline for reduced latency.

---

## 🌐 Network

| Interface | Type |
|-----------|------|
| `wlan0` | Intel Wi-Fi 7 BE200 (AX1775*/BE20*) — 802.11be 2×2 |
| `lo` | Loopback |

---

## 🔧 Kernel Parameters (GRUB)

```
GRUB_CMDLINE_LINUX_DEFAULT="intel_idle.max_cstate=1 tsx=on
usbhid.mousepoll=1 nvidia_drm.modeset=1 usbhid.kbpoll=1
pcie_aspm.policy=performance sched_itmt_enabled=1 preempt=full
pci=pcie_bus_perf pcie_ports=native vdso=2 skew_tick=1
futex_waitv=1 udev.log_priority=3 workqueue.power_efficient=false
cpufreq.default_governor=performance intel_pstate=active
threadirqs processor.max_cstate=1
usbhid.quirks=0x1b1c:0x1bac:0x40,0x331a:0x5020:0x40
usbcore.autosuspend=-1 hugepagesz=2M hugepages=2048
drm.edid_firmware=DP-3:edid/hp-x34.bin"
```

### Loaded Kernel Modules (NVIDIA)
```
nvidia_drm    nvidia_uvm    nvidia_modeset    nvidia
```

---

## 📦 Software Stack

| Component | Version |
|-----------|---------|
| Shell | zsh 5.9 (oh-my-zsh) |
| Python | 3.11.14 (+ uv 0.9.29) |
| Node.js | v22.22.2 |
| Git | 2.54.0 |
| Docker | 29.5.1 (build 2518b52d94) |
| CUDA Toolkit | 13.2 (nvcc V13.2.78) |
| GCC | 16.1.1 |
| Hermes Agent | v0.18.2 (default profile) |
| keyd | enabled + active |
| PPD (Power Profiles) | inactive |
| SDDM | active |

### Notable User Config
- **Emacs**: Doom Emacs 30.2, Wayland+XWayland (GTK3, not PGTK), classic Emacs keys (no evil), JetBrainsMono NF
- **Editor**: Zed Editor
- **Terminal**: Alacritty
- **Theme preference**: light-but-not-white (textured grays, warm off-whites), high text contrast, text shadows
- **ZSH plugins**: zsh-autosuggestions, zsh-syntax-highlighting, zsh-history-substring-search, zsh-you-should-use, zsh-z, zsh-bat
- **GRUB quirks**: cstate+sync perf tuning
- **KWin compositor**: OFF

---

## 🔄 How to Update This Spec

When any component changes (new hardware, OS upgrade, driver update, monitor change):

1. Run `skill_view(name='system-spec')` to load this spec
2. Read current values from the system (run the commands below)
3. Call `skill_manage(action='patch', name='system-spec', ...)` to update the affected table(s)

### Quick Verification Commands

```bash
# CPU
lscpu | grep -E 'Model name|CPU\(s\)|^Thread|^Core|^Socket|^L1|^L2|^L3'

# Memory
sudo dmidecode -t memory | grep -E 'Size:|Speed:|Part Number:|Configured'
cat /proc/meminfo | grep -E 'MemTotal|SwapTotal|HugePages_Total'

# GPU
nvidia-smi --query-gpu=gpu_name,driver_version,memory.total,power.limit,temperature.gpu --format=csv

# Storage
lsblk -d -o NAME,SIZE,MODEL
sudo smartctl -a /dev/nvme0 | grep -E 'Model|Firmware|Temperature|Percentage Used'
sudo smartctl -a /dev/nvme1 | grep -E 'Model|Firmware|Temperature|Percentage Used'

# Display
kscreen-doctor -o

# Audio
pactl info | grep 'Default Sink'
wpctl status | grep -A1 'Audio'

# Kernel
uname -a
cat /proc/version
cat /etc/os-release | head -3

# Network
lspci | grep -i network

# Motherboard/BIOS
sudo dmidecode -t baseboard | grep -E 'Manufacturer|Product'
sudo dmidecode -t bios | grep -E 'Vendor|Version|Release'
```
