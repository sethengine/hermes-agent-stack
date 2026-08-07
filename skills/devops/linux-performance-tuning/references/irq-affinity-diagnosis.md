# IRQ Affinity Diagnosis

Hex-to-CPU decoding table and commands for diagnosing IRQ assignments, especially on systems with isolated CPUs.

## Hex Mask to CPU Number — Quick Reference

This table maps the hex smp_affinity/effective_affinity values to CPU indices for a 20-core system. The bit position is the CPU number.

| Hex Mask | CPU | Hex Mask | CPU |
|----------|-----|----------|-----|
| `00001`  | 0   | `00100`  | 8   |
| `00002`  | 1   | `00200`  | 9   |
| `00004`  | 2   | `00400`  | 10  |
| `00008`  | 3   | `00800`  | 11  |
| `00010`  | 4   | `01000`  | 12  |
| `00020`  | 5   | `02000`  | 13  |
| `00040`  | 6   | `04000`  | 14  |
| `00080`  | 7   | `08000`  | 15  |
|         |     | `10000`  | 16  |
|         |     | `20000`  | 17  |
|         |     | `40000`  | 18  |
|         |     | `80000`  | 19  |

**Multi-CPU masks**: Combine by OR-ing the bits. Examples:
- `00003` = CPU0 + CPU1 (0x00001 | 0x00002)
- `00101` = CPU8 + CPU0 (0x00100 | 0x00001)
- `00300` = CPU9 + CPU8 (0x00200 | 0x00100)
- `000ff` = CPUs 0-7 (all isolated)
- `fff00` = CPUs 8-19 (all housekeeping)

## The Two Affinity Files

| File | Meaning |
|------|---------|
| `/proc/irq/$N/smp_affinity` | Configured affinity mask — what the kernel or user requested |
| `/proc/irq/$N/effective_affinity` | Actual runtime affinity — where interrupts actually fire |

These can differ when:
- A managed IRQ (MSI-X) was assigned by the kernel and the manual write was silently overridden
- irqbalance is running and overrode manual settings
- The requested CPU is offline

## Diagnosis Script

Run this to classify every device IRQ as "on isolated" vs "on housekeeping":

```python
#!/usr/bin/env python3
"""Classify IRQ affinities as isolated or housekeeping for a 20-CPU system."""
ISOLATED = set(range(0, 8))  # CPUs 0-7 isolated
HOUSEKEEPING = set(range(8, 20))  # CPUs 8-19 housekeeping

data = open('/proc/interrupts').read()
header = data.split('\n')[0]
cpus = [c.strip() for c in header.split() if c.strip().startswith('CPU')]
ncpus = len(cpus)

print('CPUs: %d (isolated 0-7, housekeeping 8-%d)' % (ncpus, ncpus - 1))
print('%-5s %-30s %8s %8s %-20s %-25s' % ('IRQ', 'Name', 'Affinity', 'Effective', 'CPUs', 'Status'))
print('-' * 100)

for line in data.split('\n'):
    if not any(x in line.lower() for x in
               ['nvidia', 'nvme', 'xhci', 'iwlwifi', 'snd_hda', 'igc', 'snd_sof']):
        continue
    parts = line.split()
    if not parts:
        continue
    irq = parts[0].rstrip(':')
    if not irq.isdigit():
        continue
    name = parts[-1] if parts[-1].endswith(')') else \
           (parts[-2] if len(parts) >= 2 else parts[-1])
    try:
        aff = open('/proc/irq/%s/smp_affinity' % irq).read().strip()
        eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    except IOError:
        continue
    ev = int(eff.replace(',', ''), 16)
    ec = [i for i in range(ncpus) if ev & (1 << i)]
    ec_set = set(ec)
    iso = ec_set & ISOLATED
    hk = ec_set & HOUSEKEEPING
    if iso and not hk:
        status = 'ISOLATED ONLY'
    elif iso and hk:
        status = 'SPLIT'
    else:
        status = 'housekeeping'
    cpustr = ','.join(str(c) for c in sorted(ec)) if ec else 'none'
    print('%-5s %-30s %8s %8s %-20s %-25s' % (
        irq, name[:30], aff, eff, cpustr, status))
```

## Real-World Finding: NVMe Queues on Isolated CPUs

On a system with `isolcpus=domain,managed_irq,0-7` (Arrow Lake 265K, 20 CPUs), the first 8 NVMe IO queues for each drive landed on isolated CPUs 0-7:

```
IRQ 156 nvme0q1  eff=00002 → CPU1   ISOLATED ONLY
IRQ 157 nvme0q2  eff=00010 → CPU4   ISOLATED ONLY
IRQ 158 nvme0q3  eff=00001 → CPU0   ISOLATED ONLY
IRQ 159 nvme0q4  eff=00020 → CPU5   ISOLATED ONLY
... (8 queues per drive, all on CPUs 0-7)
```

**Root cause**: The `managed_irq` flag in `isolcpus=domain,managed_irq,0-7` tells the kernel to allow managed IRQs (MSI-X, including NVMe queue completions) to target isolated CPUs. Without this flag, managed IRQs are automatically excluded.

**Fix**: Change to `isolcpus=domain,0-7` (remove `managed_irq`) — requires reboot. After reboot, NVMe queues redistribute to housekeeping CPUs automatically.
