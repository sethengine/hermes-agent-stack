# NVIDIA Xid 31 NVDEC + Chrome VA-API Crash & Latency Pattern

## Signature
```
NVRM: Xid (PCI:0000:02:00): 31, pid=<pid>, name=chrome, channel 0x09000001, intr 00000000.
  MMU Fault: ENGINE NVDEC0 HUBCLIENT_NVDEC0 faulted @ 0x1_05f6d000.
  Fault is of type FAULT_PDE ACCESS_TYPE_VIRT_WRITE
```

Every single occurrence:
- Engine: NVDEC0 (hardware video decoder)
- Process: chrome
- Fault type: FAULT_PDE (page directory entry) + VIRT_WRITE
- Same fault address across boots (`0x1_05f6d000`)
- Driver: NVIDIA 595.71.05 on RTX 5060 Ti (Blackwell)

## How Chrome Triggers It

Chrome uses VA-API for hardware video decoding. On NVIDIA, this goes through:
```
Chrome → libva → libva-nvidia-driver (0.0.17) → NVDEC engine
```

Chrome startup flags that enable this:
```
--enable-features=VaapiOnNvidiaGPUs,VaapiIgnoreDriverChecks,AcceleratedVideoDecodeLinuxGL
--render-node-override=/dev/dri/renderD128
```

`VaapiIgnoreDriverChecks` bypasses NVIDIA's driver validation — Chrome forces VA-API use even when the GPU/driver may not fully support it.

## Two Symptom Paths

### Path A: System Crash (full GPU hang → lockup → hard reset)

1. Chrome submits video decode work to NVDEC
2. GPU NVDEC engine processes the job and DMA-writes decoded frames
3. The GPU's memory mapping (page table) becomes corrupted
4. NVDEC tries to DMA-write to a stale/dead mapping → Xid 31 MMU fault
5. The corrupted GPU VA space eventually causes a full GPU hang
6. Without a hardware watchdog (iTCO_wdt blacklisted), the system stays locked until manual reset

### Path B: Input Latency / Stutter (no crash, persistent lag)

This path is the more common manifestation — the system doesn't crash, but mouse/keyboard input feels heavy, sluggish, or stuttery:

1. Chrome submits video decode work to NVDEC → Xid 31 MMU fault fires
2. NVIDIA kernel driver enters error recovery path, holding internal locks
3. KWin (Wayland compositor) renders via NVIDIA GPU — every composite command goes through the driver
4. KWin's GPU command blocks on the fault recovery lock → frame delivery delayed
5. USB mouse IRQ fires → KWin processes input → tries to composite updated frame → blocked again
6. Perceived as: cursor lags behind physical mouse movement, keyboard feels delayed

**Distinguishing latency from crash:** If the system stays up but feels sluggish, and `journalctl -k | grep 'Xid.*: 31,'` shows multiple hits, Path B is active. The Xid fault rate determines the severity — one fault per hour causes occasional hitches; one fault every few minutes causes continuous perceived lag.

## Additional Corruption (Cascade Pattern)

After multiple Xid 31 faults accumulate, the GPU VA space manager becomes progressively corrupted:

```
NVRM: nvAssertFailedNoLog: Assertion failed: vaHi <= pMemBlock->end @ gpu_vaspace.c:2022
NVRM: nvCheckFailedNoLog: Check failed: NV_OK == status @ virt_mem_allocator_gm107.c:2552
NVRM: dmaAllocMapping_GM107: can't update VA space for mapping
```

This shows the GPU's virtual address space manager is now corrupted. Every subsequent allocation from any GPU process (including the compositor) can hit this failure path, amplifying the latency. The cascade typically appears after 5-10+ Xid faults in a single boot session.

### Resched IPI Storm Correlation

When the cascade is active, the compositor's CPU core shows 20x+ more **rescheduling IPIs** than sibling P-cores:

```
# Healthy P-core:
RES: 27661  23526  19569  820837*  46274  29214  23006  814356* ...
                           ^-- CPU3 storm               ^-- CPU7 storm

# Other P-cores: 19K-46K
# Storm P-cores: 820K+ each
```

The causal chain: Xid 31 → NVIDIA fault handler blocks → compositor GPU command blocks → compositor scheduler is forced to reschedule waiting tasks → other processes wake on different CPUs → cross-CPU wakeups generate rescheduling IPIs → compositor core gets bombarded with IPIs → further compositor delay.

### I/O Pressure Interaction

Check `/proc/pressure/io` — a system with active Xid 31 cascade often shows `full total > 10M`:

```
some avg10=0.00 total=101266786
full avg10=0.00 total=97594861    <-- 97M full I/O stalls (processes blocked on I/O)
```

The compositor's frame scheduling pipeline is sensitive to any blocking — when Chrome renderers (which share the NVIDIA GPU display context) block on I/O, the compositor's frame pacing is disrupted.

## Diagnostic Flow

### Quick check (is Xid 31 the cause of input lag?)

```bash
# 1. Count faults this boot
journalctl -k --no-pager | grep -c 'Xid.*: 31,'

# 2. Check for cascade corruption
journalctl -k --no-pager | grep -c 'gpu_vaspace.c:2022\|virt_mem_allocator_gm107.c:2552'

# 3. Is the compositor on a storm CPU?
ps -eo tid,psr,comm | grep -i "kwin\|compiz\|mutter"
# Compare against:
grep "RES" /proc/interrupts | awk '{for(i=2;i<=20;i++) print (i-2), $i}' | sort -k2 -rn | head -5

# 4. Is Chrome actively using NVDEC?
nvidia-smi pmon -c 1 | grep chrome

# 5. I/O pressure compounding?
cat /proc/pressure/io | grep full
```

**If Xid 31 count > 5 AND compositor CPU has 20x+ resched IPIs AND I/O full > 10M:**
→ Chrome NVDEC is causing input latency via the GPU fault → compositor block chain.

### One-shot per-boot monitoring script

```bash
#!/bin/bash
# Run at boot to track Xid 31 latency impact
journalctl -k --no-pager --since="5 minutes ago" | grep -c 'Xid.*: 31,' > /tmp/xid31_count
grep "RES" /proc/interrupts | awk '{print "CPU" (NR-1) ":" $2}' > /tmp/resched_dist
cat /proc/pressure/io | grep full > /tmp/io_pressure
```

## Driver Versions Affected

- NVIDIA 595.71.05 (confirmed on RTX 5060 Ti)
- libva-nvidia-driver 0.0.17-1
- Kernel 7.0.10-1-MANJARO

## External Reports

- [elFarto/nvidia-vaapi-driver #298](https://github.com/elFarto/nvidia-vaapi-driver/issues/298) — "Watching videos sometimes causes artifacts on the GPU" — Xid 31 + 109, closed as `nvidia-issue` by maintainer
- [elFarto/nvidia-vaapi-driver #359](https://github.com/elFarto/nvidia-vaapi-driver/issues/359) — "Firefox media decoder crashes since v137" — "NVRM: VM: invalid mmap" flood (same root cause)
- [elFarto/nvidia-vaapi-driver #253](https://github.com/elFarto/nvidia-vaapi-driver/issues/253) — "Failure after suspend/resume?" — open since 2023, tagged `nvidia-issue`

Maintainer position: Xid 31 MMU faults from NVDEC are an NVIDIA kernel module or GPU firmware bug. The VA-API wrapper is just the path that triggers it.

## Resolution

### Immediate (latency + crash)
1. `chrome://flags/#disable-accelerated-video-decode` → Enabled
2. Or launch Chrome with `--disable-accelerated-video-decode`
3. After disable: verify Xid 31 stops with `journalctl -k --no-pager | grep -c 'Xid.*: 31,'` after 30 minutes
4. If resched IPI storm persists on compositor core (unlikely after fix, but possible from other causes): pin KWin to E-cores: `sudo taskset -pac 0xfff00 $(pgrep kwin_wayland)`

### Alternative Backend
`/usr/lib/dri/nvidia_vulkan_drv_video.so` uses Vulkan Video extensions instead of direct NVDEC. May avoid the bug.

### Watchdog Recovery
Remove `modprobe.blacklist=iTCO_wdt` from kernel cmdline and rebuild GRUB. This gives ~60s auto-reboot on GPU hang instead of permanent lockup requiring manual reset.
