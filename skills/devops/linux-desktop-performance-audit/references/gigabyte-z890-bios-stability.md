# Gigabyte Z890 AERO G BIOS Stability Settings

Authoritative reference for hardware audit + BIOS stability optimization on Gigabyte Z890 + Intel Arrow Lake (Core Ultra 200 series). Produced from live session: manual analysis, community research (Overclock.net, SkatterBencher, Reddit), driver/firmware review, and hardware probing.

## Current System Profile

| Component | Detail |
|-----------|--------|
| **Motherboard** | Gigabyte Z890 AERO G (Rev. 1002) — ATX, LGA1851, Z890 Express |
| **BIOS** | F17f (Jul 2025) → **latest: F21 (Jun 2026)** |
| **CPU** | Intel Core Ultra 7 265K (Arrow Lake-S, 8P+12E, no HT) |
| **GPU** | NVIDIA RTX 5060 Ti (GB206) — PCIe 4.0 x8 (⚠️ possible lane issue) |
| **RAM** | 64 GB DDR5 (likely 4×16 GB from 4 SPD temp sensors) |
| **Storage** | WD_BLACK SN850X 2 TB (PCIe 4.0 x4) + Kingston A2000 1 TB (PCIe 3.0 x4) |
| **Monitor** | HP X34 (3440×1440 @ 60 Hz) — via GPU HDMI |
| **OS** | Manjaro, Kernel 7.0.10-1-MANJARO |
| **Audio** | Realtek ALC1220 (custom PipeWire sink, EasyEffects chain) |

## Commands for BIOS-Level Hardware Inspection

Run these to gather all BIOS-visible data from within Linux:

### BIOS version + date
```bash
sudo dmidecode -t 0 2>/dev/null | grep -E "Version|Date|Release"
# Or without sudo:
cat /sys/devices/virtual/dmi/id/bios_version
cat /sys/devices/virtual/dmi/id/bios_date
```

### Board identification
```bash
cat /sys/devices/virtual/dmi/id/board_{vendor,name,version}
cat /sys/devices/virtual/dmi/id/product_{name,version}
```

### PCIe link verification (critical: spot lane-sharing issues)

```bash
# GPU PCIe width + speed — should match expected slot config
cat /sys/bus/pci/devices/0000:02:00.0/current_link_speed
cat /sys/bus/pci/devices/0000:02:00.0/current_link_width

# NVMe slot speeds
cat /sys/bus/pci/devices/0000:01:00.0/current_link_speed  # SN850X
cat /sys/bus/pci/devices/0000:03:00.0/current_link_speed  # A2000
```

If GPU shows **x8** when it should be **x16**, suspects:
- PCIEX8 slot populated (auto-doubles to x8/x8 with PCIEX16)
- M.2 slot stealing PCIe lanes (check manual: M2A_CPU uses CPU lanes on some configs)
- GPU reseat needed

### DDR5 SPD temperature monitoring
DDR5 dimms have onboard SPD hubs that report temperature. These show as `spd5118-i2c-*` sensors:
```bash
sensors | grep spd5118
```

### CPU per-core topology + max clock
```bash
lscpu -e
```
Core 0-7 = P-cores (5.4-5.5 GHz max). Cores 8-19 = E-cores (4.6 GHz max). Cores 12-13 = LPE (Low Power E) cores at 6.5 GHz.

### GPU power state under load
```bash
nvidia-smi --query-gpu=name,driver_version,pcie.link.width.current,pcie.link.gen.current,memory.total,power.limit --format=csv,noheader
```

## BIOS Update — Q-Flash Plus Procedure (no CPU/RAM needed)

| Step | Action |
|------|--------|
| 1 | Format USB drive to **FAT32** |
| 2 | Download latest BIOS .zip from [support page](https://www.gigabyte.com/Motherboard/Z890-AERO-G/support) |
| 3 | Extract, rename the .F2x file to **gigabyte.bin** |
| 4 | Copy `gigabyte.bin` to USB root |
| 5 | Insert USB into **Q-Flash Plus** designated port (check manual — usually a specific white/red USB 2.0 port on back panel) |
| 6 | **System OFF** (S5 state, PSU still plugged in) |
| 7 | Press **Q-Flash Plus button** — LED blinks during flash |
| 8 | Wait for LED to go solid (3-5 minutes). Do NOT power off. |

Latest BIOS: F21 (Jun 11, 2026, checksum 4F9F). Key jumps per version:
- **F18** → Arrow Lake 2-series CPU support, Secure Boot default, CSME 19.0.5.2018
- **F19** → CPU microcode rev 121, CSME 19.0.5.2175, GOP 1068
- **F21a** → HUDIMM support, memory compatibility
- **F21b** → D5 Single Boost technology
- **F21** → Security + stability improvements

## BIOS Settings for Stability (Enter BIOS → Tweaker tab)

### PerfDrive Profile Selection

| Profile | Power | Temp | Performance | Use Case |
|---------|-------|------|-------------|----------|
| Intel Default — Performance | 250W+ | High | Stock baseline | Out of box reference |
| Intel Default — Baseline | 125W | Low | -30% | Crisis recovery |
| **Spec Enhance** ✅ | ~240W | ~82°C | +3-5% | **Best for daily stability** |
| Optimization | ~250W | ~91°C | +3-6% | Faster but hotter |
| Unleash | 300W+ | 97-105°C | +5-8% | OC only — excessive voltage |

**Recommendation:** `Spec Enhance` — balances performance gain vs voltage/heat. Avoid `Unleash` on air cooling; it pushes DLVRin >1.5V on some boards.

### CPU Settings (Advanced CPU Settings submenu)

| Setting | Recommended | Notes |
|---------|-------------|-------|
| **Intel Turbo Boost Technology** | Enabled | Core boost required for rated clocks |
| **Enhanced Multi-Core Performance** | Auto/Disabled | Auto variant can overvolt |
| **C-States** | C1E=Enabled, Package C6/C10 | Saves idle power — NOT a bottleneck for desktop responsiveness |
| **Energy Efficient Turbo** | **Disabled** | Prevents voltage sag under burst loads |
| **CEP — IA CEP** | **Disabled** | **Critical.** Prevents VRM current limiting that causes performance regression. Required if undervolting. |
| **CEP — GT CEP** | Auto (Enabled) | Safe to leave for iGPU stability |
| **CEP — SA CEP** | Auto (Enabled) | Leave for memory controller stability |
| **CPU Thermal Monitor** | Enabled | Safety throttle |
| **Tcc Activation Offset** | 0 | Default — don't reduce throttle point |
| **TJMAX** | 105°C | Standard Arrow Lake limit |
| **Intel Speed Shift Technology** | Enabled | Better responsiveness |
| **CPU EIST** | Enabled | Allows idle frequency reduction |

### Power Limits (Turbo Power Limits)

| Setting | Recommended (Stock) | Notes |
|---------|-------------------|-------|
| **Package Power Limit 1 (TDP)** | **250W** | Match CPU TDP |
| **Package Power Limit 2** | **250W** | Equal for consistent sustained performance |
| **Power Limit 1 Time Window** | Auto (or 448s) | |
| **ICC Max** | **347A** (stock) | |

### Memory Settings (Advanced Memory Settings)

| Setting | Recommended | Notes |
|---------|-------------|-------|
| **XMP/EXPO Profile** | Profile 1 | Enable XMP for rated speed |
| **High Bandwidth Enable** | **Enabled** | Free bandwidth uplift |
| **Low Latency Enable** | **Enabled** | Free latency reduction |
| **Memory Enhancement** | Auto (or Enhanced) | Enhanced = tightens subtimings |
| **Gear Down Mode** | Enabled | Signal integrity at high speed |
| **Power Down Enable** | **Disabled** | Reduces latency (may conflict with ASPM Linux power saving) |
| **Memory Ref Frequency** | Auto | |

⚠️ **4 DIMM DDR5 caution:** Running 4 sticks of DDR5 at high XMP speeds is unstable on Z890. If crashes occur:
1. Lower speed one notch (e.g., 6400→6000)
2. Add +0.02V to VDD/VDDQ
3. Best stability: 2 sticks in A2/B2 slots

### Voltage Settings (leave Auto for stability — only adjust if undervolting)

Do NOT change these for stock stability. If undervolting:

| Setting | Stock | Undervolt Target |
|---------|-------|-----------------|
| AC Loadline | Auto (varies) | 0.5 mOhm (reduces VID under load) |
| DC Loadline | Auto | 1.0 mOhm (match LLC impedance) |
| IA VR Voltage Limit | Auto | 1400 mV (cap max voltage) |
| VCCSA (System Agent) | Auto | Auto — SA voltage is **very sensitive** on Arrow Lake |

When undervolting: IA CEP must be Disabled first, or the CPU will drop performance to compensate.

## Community Stability Notes (from Overclock.net Z890 owners)

### Caffinator's 265KF Daily Settings (verified: y-cruncher 3h + Prime95 12h)
- PerfDrive: Spec Enhance
- Ring 40x, NGU/D2D 32x
- Memory: 32-44-44-90 @ DDR5-7200, High Bandwidth/Low Latency Enabled
- CPU Vcore: Adaptive 1.25V + 0.035V offset
- C-states: Enabled (but Energy Efficient Turbo = Disabled)
- System Agent: 1.150V
- Temps: 79-83°C OCCT, 236-242W

### Common Arrow Lake pitfalls on Gigabyte Z890
1. **GPU lane width** — PCIEX16 drops to x8 if PCIEX8 or specific M.2 slot is populated
2. **D2D cold boot** — D2D ratio above 33× may cause cold boot failure; stay at 30-32× for stability
3. **E-core overclocking** — Going above stock 46× on E-cores introduces browser crashes and WHEA errors on many samples
4. **BIOS F20 instability** — Some users report cold boot failures with ERP/Powerloading enabled on F20; rolled back to F19
5. **TRCDW** — Only adjustable on BIOS F20+ (F17f does not have it)
6. **VRM thermal corner** — The Z890 AERO G's VRM can sustain ~250W without active airflow; sustained 300W+ may require chassis fan over VRM

## Reference Sources

- [Gigabyte Z890 AERO G Manual PDF](https://download.gigabyte.com/FileList/Manual/mb_manual_z890-aero-g_1005_e.pdf)
- [Gigabyte Intel 800 BIOS Setup Manual](https://download.gigabyte.com/FileList/Manual/mb_manual_intel800-bios_e_v2.pdf)
- [SkatterBencher #87: 265K to 5700 MHz](https://skatterbencher.com/2025/06/18/skatterbencher-87-core-ultra-7-265k-overclocked-to-5700-mhz/)
- [Caffinator's 265KF OC Guide (Overclock.net)](https://www.overclock.net/threads/my-z890-arrow-lake-265kf-oc-settings.1818547/)
- [Gigabyte Z890 Owner's Thread (Overclock.net)](https://www.overclock.net/threads/gigabyte-aorus-z890-owners-thread.1814647/)
- [Gigabyte UC BIOS — New Features](https://bd.aorus.com/blog-detail.php?i=1322)
- [Gigabyte Z890 Support (BIOS downloads)](https://www.gigabyte.com/Motherboard/Z890-AERO-G/support)
