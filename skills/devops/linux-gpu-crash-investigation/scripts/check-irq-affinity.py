#!/usr/bin/env python3
"""Analyze IRQ affinities relative to isolated/nohz_full CPUs."""
import sys

data = open('/proc/interrupts').read()
header = data.split('\n')[0]
cpus = [c.strip() for c in header.split() if c.strip().startswith('CPU')]
ncpus = len(cpus)

# Read nohz_full CPUs
nohz = set()
try:
    with open('/sys/devices/system/cpu/nohz_full') as f:
        for r in f.read().strip().split(','):
            if '-' in r:
                lo, hi = map(int, r.split('-'))
                nohz.update(range(lo, hi+1))
            elif r:
                nohz.add(int(r))
except:
    pass

# Read isolated CPUs
isol = set()
try:
    with open('/sys/devices/system/cpu/isolated') as f:
        for r in f.read().strip().split(','):
            if '-' in r:
                lo, hi = map(int, r.split('-'))
                isol.update(range(lo, hi+1))
            elif r:
                isol.add(int(r))
except:
    pass

# Filter by device types
targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {'nvidia','usb','nvme','xhci','iwlwifi'}

def mask2cpus(mask_str):
    v = int(mask_str.replace(',',''), 16)
    return [i for i in range(ncpus) if v & (1<<i)]

print(f'CPUs: {ncpus} total | nohz_full: {sorted(nohz) if nohz else "none"} | isolcpus: {sorted(isol) if isol else "none"}')
print(f'{"IRQ":>5} {"Device":<35} {"Affinity":>8} {"CPUs":<20} {"Status":<30}')
print('-'*110)

for line in data.split('\n'):
    if not any(t in line.lower() for t in targets):
        continue
    parts = line.split()
    if not parts or not parts[0].rstrip(':').isdigit():
        continue
    irq = parts[0].rstrip(':')
    dev = ' '.join(parts[ncpus+1:]) if len(parts) > ncpus+1 else '?'

    try:
        eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    except:
        continue
    ec = mask2cpus(eff)

    # Classify
    nohz_hits = [c for c in ec if c in nohz]
    iso_hits  = [c for c in ec if c in isol]
    status_parts = []
    if nohz_hits:
        status_parts.append('NO_HZ_FULL!')
    if iso_hits:
        status_parts.append('ISOLATED!')
    if not status_parts:
        status_parts.append('OK')

    cpustr = ','.join(str(c) for c in sorted(ec)) if ec else 'none'
    status = ' '.join(status_parts)
    print(f'{irq:>5} {dev:<35} {eff:>8} {cpustr:<20} {status:<30}')
