---
name: linux-gpu-crash-investigation
description: Investigate system crashes and restarts caused by GPU (NVIDIA) driver faults. Covers Xid error analysis, journalctl boot forensics, IRQ affinity verification, Chrome VA-API decode conflicts, and kernel cmdline interaction diagnosis.
argument-hint: "[NVIDIA Xid error type] [GPU model] [symptoms]"
allowed-tools: Bash, Read, Write, Search, WebSearch, Browser
user-invocable: true
---

# Linux GPU Crash Investigation

## When to Use
- System spontaneously reboots or hard-locks with no clean shutdown in journal
- `journalctl --list-boots` shows short uptime sessions ending abruptly
- Persistent mouse/keyboard input latency on NVIDIA + Wayland without obvious cause
- Compositor (KWin, Mutter, etc.) stutters or frame drops while GPU is under load
- NVIDIA Xid errors in kernel log (`dmesg | grep Xid` or `journalctl -k | grep NVRM`)
- GPU video decode (Chrome, Firefox, mpv) triggers crashes
- User has custom kernel parameters (`nohz_full`, `isolcpus`, `iommu`, `pcie_aspm`) and suspects interaction

## Methodology (Ordered)

### Phase 1: Boot Forensics
```
journalctl --list-boots 2>/dev/null
```
- Identify boots with unusually short durations (minutes, not days)
- Check if the previous boot ended cleanly: `journalctl -b -1 --no-pager 2>/dev/null | tail -20`
- A **clean shutdown** contains: `Reached target System Shutdown`, `systemd-reboot.service`, `Sending SIGTERM to remaining processes`, `Journal stopped`
- An **abrupt crash** has none of these — just a sudden gap before the next boot starts

### Phase 2: Kernel Crash Signatures
```
journalctl -b -1 -k --no-pager 2>/dev/null | grep -iE 'Xid|panic|oops|bug|Call Trace|lockup|hung_task|rcu.*stall|watchdog|MCE'
```
- **Xid errors** are GPU hardware faults — the GPU itself reports the error
- Key Xid types:
  - **Xid 31**: MMU fault (page table / memory mapping error)
    - Common trigger: Chrome VAAPI video decode hitting NVDEC0 on NVIDIA open module
    - Escalation path: Xid 31 → BAR1 VA space exhaustion → Xid 154 (Node Reboot Required)
    - On RTX 5060 Ti 595.71.05: also linked to GSP firmware halt under NVDEC0 workload
  - **Xid 13**: Graphics engine fault
  - **Xid 109**: Context switch timeout (often precedes Xid 31)
  - **Xid 61**: Internal micro-controller error
  - **Xid 120**: GSP task exception (load access page fault on GSP RISC-V core)
    - Indicates the GSP RISC-V co-processor crashed internally
    - Common on Blackwell (RTX 50-series) with nvidia-open module
    - Often followed by Xid 154 within seconds
    - Diagnostic: journal shows `GSP-CrashCat Report`, RISC-V register state dump
  - **Xid 154**: Node Reboot Required (unrecoverable GPU state)
    - Driver determined fullchip reset is needed but the reset itself failed
    - Often follows Xid 31 or Xid 120 as the escalation
    - On Blackwell + nvidia-open: cannot be recovered — requires hardware power cycle
    - `nvidia-smi` hangs, `systemctl reboot` hangs at nvidia_drm teardown
  - **Xid 175**: GSP RPC timeout (GSP stopped responding to host driver)
    - Occurs ~75s after the initial GSP crash
    - Final confirmation that GSP firmware is irrecoverably wedged
- **GSP crash cascade on Blackwell (RTX 50-series):**
  The GSP firmware crash on Blackwell + nvidia-open follows a distinct pattern:
  1. Trigger event (e.g., NVDEC0 under Chrome, CUDA workload)
  2. Xid 120 — GSP RISC-V core exception (page fault or halt)
  3. Xid 175 — GSP RPC timeout (~75s later, driver polls GSP, gets no response)
  4. Display freezes — vblank counter stops updating (Xid 16)
  5. Xid 154 — Node Reboot Required (driver declares unrecoverable)
  6. Fullchip reset attempt fails — every reset precondition assertion errors
  7. System hard-locked — `nvidia-smi` hangs, only hardware power button works
  - GSP firmware **cannot be disabled** on nvidia-open + Blackwell
  - Switching to the proprietary `nvidia` kernel module is not an option (does not support Blackwell)
  - Known on RTX 5060 Ti (CachyOS forum), RTX 5070 (NVIDIA Dev Forum), RTX 5080/5090 eGPU
- **PCIe link training as crash factor:**
  Blackwell GPUs have known PCIe Gen 5 stability issues that can cause link drops or training failures, sometimes presenting as GPU crashes. Check current link status:
  ```bash
  sudo lspci -vv -s $(lspci | grep NVIDIA | cut -d' ' -f1) | grep -A2 'LnkSta:'
  ```
  - Expected: `Speed 32GT/s (Gen 5), Width x16` on a Gen5-capable slot
  - If `(downgraded)` appears: the initial PCIe training failed at Gen 5 and fell back — this is a known issue on RTX 50-series
  - Reducing to Gen 4 in BIOS may improve stability (negligible performance impact)
- If no kernel panic/Oops is found but the system reboots: check for hardware watchdog or GPU hang that locked the system with no kernel log

### Phase 3: GPU Process Attribution
Xid errors contain the triggering process. Extract:
```
journalctl -b -3 -k --no-pager | grep 'Xid' | grep -oP 'pid=\d+, name=\S+'
```
- Common triggers: `chrome` (NVDEC video decode), `firefox`, game processes
- If `chrome` + `NVDEC0`: VA-API video decode is the path → check Chrome GPU flags

### Phase 4: Chrome VA-API / NVDEC Conflict
When Chrome triggers Xid 31 on NVDEC:
```
ps aux | grep chrome | grep -oP 'enable-features=[^ ]*' | tr ',' '\n' | grep -iE 'vaapi|video|decode|nvidia|gpu'
```
- `VaapiOnNvidiaGPUs` + `VaapiIgnoreDriverChecks` = forcing VA-API through NVIDIA NVDEC bypassing safety checks
- Check installed driver: `pacman -Q libva-nvidia-driver`
- Check GPU driver: `nvidia-smi` or `pacman -Q nvidia-utils`
- External reference: `references/nvidia-xid31-chrome-vaapi.md`

### Phase 5: Kernel Cmdline Interaction Analysis
When user has custom kernel parameters (`nohz_full`, `isolcpus`, `rcu_nocbs`, `intel_iommu`):
1. Check `/proc/cmdline` for current boot
2. Check previous boots: `journalctl -b -1 -k | grep 'Command line'`
3. Compare IRQ affinities: `cat /proc/interrupts | grep -iE 'nvidia|usb|nvme|xhci'`
4. Check nohz_full CPUs: `cat /sys/devices/system/cpu/nohz_full`
5. Rule out: if GPU IRQs land on CPUs **not** in nohz_full, the kernel tick config isn't the cause

### Phase 6: Latency Impact Assessment (not just crashes)

Xid 31 fault storms can cause **perceived input/mouse latency** without any system crash or reboot. If the user reports stuttering, lag, or "heavy" input (not full crashes), do this layer of diagnostics:

```bash
# 1. Count Xid 31 occurrences in this boot
journalctl -k --no-pager | grep -c 'Xid.*: 31,'

# 2. Check if VA space corruption has started (cascade errors)
journalctl -k --no-pager | grep -c 'gpu_vaspace.c:2022\|virt_mem_allocator_gm107.c:2552'

# 3. Check compositor CPU placement against resched IPI storm
echo "=== NVIDIA IRQ CPUs ==="
grep "nvidia" /proc/interrupts | head -5
echo "=== Compositor CPU ==="
ps -eo tid,psr,comm | grep -i "kwin\|compiz\|mutter" | head -5
echo "=== Resched IPI distribution ==="
grep "RES" /proc/interrupts | awk '{for(i=2;i<=20;i++) print (i-2), $i}' | sort -k2 -rn | head -5

# 4. Check I/O pressure (contributing to compositor stalls)
cat /proc/pressure/io

# 5. Check if NVIDIA GPU is in HMM mode (increases TLB shootdowns)
nvidia-smi -q 2>/dev/null | grep "Addressing Mode"

# 6. Check if Chrome is actively faulting now
nvidia-smi pmon -c 1 2>/dev/null | grep chrome
```

**The latency chain:** GPU fault → NVIDIA driver enters error recovery → driver holds internal locks → compositor (rendering via NVIDIA) issues composite command → blocks on fault handler → frame drops → cursor stutters → perceived mouse lag.

**Key signals that Xid 31 is causing latency (not just crashes):**
- Compositor PID's CPU matches a CPU with 20x+ more resched IPIs than sibling P-cores
- `/proc/pressure/io` shows `full` total > 10M (I/O stalls compounding compositor scheduling)
- `nvidia-smi pmon` shows Chrome as `C+G` (compute + graphics) — indicates active NVDEC workload
- VA space assertion failures in journal (`gpu_vaspace.c:2022`) — indicates cumulative corruption

**Resched IPI storm diagnosis:**
Compare the RES line in `/proc/interrupts` across P-cores. A healthy P-core on a nohz_full system has <50K resched IPIs. Storm levels are 800K+ on specific cores. The compositor running on a storm-affected core is the primary latency delivery mechanism.

### Phase 7: External Source Verification
- Check GitHub issues: `elFarto/nvidia-vaapi-driver` for matching Xid patterns
- NVIDIA Developer Forums: `forums.developer.nvidia.com` — search Xid type + GPU model
- Arch BBS: `bbs.archlinux.org` — search driver version + error signature
- The `nvidia-issue` label on the VA-API driver repo means the maintainer attributes it to NVIDIA's kernel module, not the wrapper

## Pitfalls
- **Don't blame the wrapper first**: Xid errors are GPU hardware-level faults. Even though the VA-API wrapper triggers them, the bug is in the NVIDIA kernel module or GPU firmware.
- **Don't remove useful kernel params**: `nohz_full` and `rcu_nocbs` reduce kernel noise without causing GPU faults. Only `isolcpus` can worsen crashes by creating core contention.
- **iTCO_wdt blacklist**: If `modprobe.blacklist=iTCO_wdt` is in cmdline, there's no hardware watchdog — a GPU hang means manual reset required. Re-enabling it gives ~60s auto-reboot on lockup.
- **CMOS battery**: If a boot's FIRST entry timestamp is AFTER its LAST entry, the system lost RTC time during the outage — usually from a hard power loss.

## Support Files
- `references/nvidia-xid31-chrome-vaapi.md` — Complete reference for the Xid 31 NVDEC + Chrome VA-API crash pattern, including external GitHub issue links and driver versions
- `scripts/check-irq-affinity.py` — Analyzes IRQ affinities against nohz_full/isolcpus CPUs, classifying each device IRQ as OK or problematic

## Resolution Paths
1. **Immediate (latency + crash)**: Disable Chrome GPU video decode (`chrome://flags/#disable-accelerated-video-decode` → Enabled). This stops the NVDEC0 fault cycle at the source and resolves both crash and latency symptoms.
2. **Latency-specific**: After disabling video decode, if resched IPI storms remain on compositor cores, pin the compositor to E-cores (e.g. `taskset -pac 0xfff00 $(pgrep kwin_wayland)`) to prevent P-core IPI interference.
3. **Alternative backend**: Try `/usr/lib/dri/nvidia_vulkan_drv_video.so` (Vulkan Video path instead of NVDEC direct)
4. **Blackwell GSP crash — PCIe Gen 4 workaround**: Force PCIe Gen 4 in BIOS (instead of Auto/Gen 5). Blackwell GPUs have known PCIe 5.0 stability issues that can trigger or worsen GSP crashes. Negligible performance impact.
5. **Blackwell GSP crash — try different driver branch**: The 580 or 575 branch has different GSP firmware blobs that may be more stable. The 595 branch has the most GSP crash reports. Check the NVIDIA Unix Driver Archive for available branches.
6. **vBIOS update for RTX 5060 Ti**: NVIDIA released a UEFI firmware update tool for RTX 5060 series to fix blank-screen-on-reboot issues. This does NOT fix in-use GSP crashes but may improve overall stability. Windows .exe only.
7. **Wait for fix**: Track `elFarto/nvidia-vaapi-driver` issues and NVIDIA Developer Forum for GSP firmware updates. NVIDIA is tracking Blackwell GSP issues.
8. **Downgrade**: If older driver supports the GPU, test pre-595 series — but RTX 5060 Ti requires 595.x+
