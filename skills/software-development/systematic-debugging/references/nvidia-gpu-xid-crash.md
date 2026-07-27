# NVIDIA GPU Xid Crash Investigation

## Quick Recognition

When a system reboots itself with no clean shutdown message in journalctl, check for GPU Xid errors immediately:

```bash
# List all boots to find crash patterns
journalctl --list-boots

# Check kernel logs for Xid errors across recent boots
for b in -1 -2 -3 -4; do
  count=$(journalctl -b $b -k --no-pager 2>/dev/null | grep -c 'Xid')
  [ "$count" -gt 0 ] && echo "Boot $b: $count Xid errors"
done
```

## The Xid 31 NVDEC Pattern

**Signature:**
```
NVRM: Xid (PCI:0000:02:00): 31, pid=..., name=chrome, channel ...
    MMU Fault: ENGINE NVDEC0 HUBCLIENT_NVDEC0 faulted @ 0x...
    Fault is of type FAULT_PDE ACCESS_TYPE_VIRT_WRITE
```

**Key indicators:**
- ENGINE = NVDEC0 (hardware video decoder)
- Process = `chrome` (or `firefox`)
- Always FAULT_PDE ACCESS_TYPE_VIRT_WRITE
- Same fault address recurring (e.g., `0x1_05f6d000`)

## Diagnostic Workflow

### Step 1: Count Xid errors per boot session

```bash
journalctl -b -1 -k --no-pager | grep -c 'Xid'
journalctl -b -2 -k --no-pager | grep -c 'Xid'
```

### Step 2: Get the unique error signatures

```bash
journalctl -b -3 -k --no-pager | grep 'Xid.*:' | sort -u
```

### Step 3: Check if Chrome is using VA-API with dangerous flags

```bash
ps aux | grep chrome | grep -oP 'enable-features=[^ ]*' | tr ',' '\n' | grep -iE 'vaapi|video|decode|nvidia|gpu'
```

**Red flag flags:**
- `VaapiIgnoreDriverChecks` — bypasses NVIDIA GPU validation, directly triggers MMU faults
- `VaapiOnNvidiaGPUs` — enables VA-API on non-Intel GPUs (required for NVIDIA but risky)

### Step 4: Check the VA-API driver version

```bash
pacman -Q libva-nvidia-driver
ls /usr/lib/dri/nvidia*drv_video*
```

Two backends exist:
- `nvidia_drv_video.so` — direct NVDEC backend (triggers Xid 31 on Blackwell)
- `nvidia_vulkan_drv_video.so` — Vulkan Video backend (safer alternative)

### Step 5: Check IRQ distribution for GPU

```bash
cat /proc/interrupts | grep -i nvidia
```

Look for whether GPU IRQs are on the same cores as the application (contention increases crash likelihood).

### Step 6: Cross-reference against external sources

Search GitHub issues on `elFarto/nvidia-vaapi-driver`:
- Issues tagged `nvidia-issue` = maintainer confirms it's an NVIDIA driver bug, not the VA-API wrapper
- Xid 31 + NVDEC0 is a known Blackwell (RTX 5060/5070 Ti) driver bug
- Confirmatory pattern: also check for `NVRM: VM: invalid mmap` floods

## Crash Mechanism

1. Chrome allocates GPU-mapped DMA buffers for video frames via VA-API
2. NVIDIA NVDEC engine DMA-writes decoded frames to those buffers
3. GPU virtual address space corruption causes page table entries to go stale
4. NVDEC0 tries to write to a now-invalid VA → MMU fault (Xid 31)
5. Accumulated faults corrupt GPU state → GPU hang → system lockup → forced reset

## Root Cause Classification

| Component | Bug? |
|-----------|------|
| NVIDIA 595.71.05 kernel module (Blackwell NVDEC) | **Yes** — MMU fault in NVDEC0 |
| libva-nvidia-driver 0.0.17 (VA-API wrapper) | Partial — exposes the driver bug |
| Chrome `VaapiIgnoreDriverChecks` flag | Trigger — bypasses GPU validation |
| `nohz_full` / `rcu_nocbs` / IRQ pinning | **No** — not causal, but isolcpus worsens it via core contention |

## Fix Priority

1. **Remove `VaapiIgnoreDriverChecks`** — keeps GPU decode but allows driver to safely reject unsupported configs
2. **Switch to Vulkan Video backend** — `export LIBVA_DRIVER_NAME=nvidia-vulkan` (uses different API path, avoids NVDEC direct)
3. **Disable GPU video decode entirely** — `chrome://flags/#disable-accelerated-video-decode`
4. **Re-enable iTCO_wdt watchdog** — remove `modprobe.blacklist=iTCO_wdt` so locked GPU auto-reboots in ~60s
5. **Upgrade NVIDIA driver** — check `nvidia-beta` AUR package for pre-release fixes

## Supporting Tool: IRQ Affinity Inspector

Save as `/tmp/check_irq.py` and run to see which device interrupts land on which CPUs:

```python
#!/usr/bin/env python3
data = open('/proc/interrupts').read()
header = data.split('\n')[0]
ncpus = len([c for c in header.split() if c.startswith('CPU')])

for line in data.split('\n'):
    if not any(x in line.lower() for x in ['nvidia','usb','nvme','xhci','iwlwifi']):
        continue
    parts = line.split()
    if not parts or not parts[0].rstrip(':').isdigit():
        continue
    irq = parts[0].rstrip(':')
    name = parts[-1][:30]
    try:
        aff = open('/proc/irq/%s/smp_affinity' % irq).read().strip()
        eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    except:
        continue
    ev = int(eff.replace(',',''), 16)
    ec = [i for i in range(ncpus) if ev & (1<<i)]
    iso = [c for c in ec if c < 8]  # adjust threshold for P-core count
    status = '\u26a0 ISOLATED' if iso and not [c for c in ec if c >= 8] else '\u2713 housekeeping'
    cpustr = ','.join(str(c) for c in sorted(ec)) if ec else 'none'
    print('IRQ %-3s %-30s %-20s %-25s' % (irq, name, cpustr, status))
```
