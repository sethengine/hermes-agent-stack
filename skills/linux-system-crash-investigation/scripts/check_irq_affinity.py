#!/usr/bin/env python3
"""Check IRQ affinities and classify by isolated vs housekeeping CPUs."""
data = open('/proc/interrupts').read()
header = data.split('\n')[0]
cpus = [c.strip() for c in header.split() if c.strip().startswith('CPU')]
ncpus = len(cpus)

# Determine isolated/housekeeping split
try:
    isolated_str = open('/sys/devices/system/cpu/isolated').read().strip()
    isolated = set()
    for r in isolated_str.split(','):
        if '-' in r:
            lo, hi = r.split('-')
            isolated.update(range(int(lo), int(hi)+1))
        else:
            isolated.add(int(r))
except:
    isolated = set(range(8))  # fallback: assume 0-7 isolated

print('CPUs: %d (isolated %s, housekeeping %s)' % (
    ncpus,
    ','.join(str(c) for c in sorted(isolated)),
    ','.join(str(c) for c in range(ncpus) if c not in isolated)
))
print('%-5s %-30s %8s %8s %-20s %-25s' % ('IRQ', 'Name', 'Affinity','Effective','CPUs','Status'))
print('-'*100)

filter_devices = ['nvidia','usb','nvme','xhci','iwlwifi','vpu']
filter_arg = None  # set to a list to override

for line in data.split('\n'):
    devs = filter_devices if filter_arg is None else filter_arg
    if not any(x in line.lower() for x in devs):
        continue
    parts = line.split()
    if not parts:
        continue
    irq = parts[0].rstrip(':')
    if not irq.isdigit():
        continue
    name = parts[-1] if parts[-1].endswith(')') else (parts[-2] if len(parts) >= 2 else parts[-1])
    try:
        aff = open('/proc/irq/%s/smp_affinity' % irq).read().strip()
        eff = open('/proc/irq/%s/effective_affinity' % irq).read().strip()
    except:
        continue
    av = int(aff.replace(',',''), 16)
    ev = int(eff.replace(',',''), 16)
    ec = [i for i in range(ncpus) if ev & (1<<i)]
    iso_on = [c for c in ec if c in isolated]
    hk_on  = [c for c in ec if c not in isolated]
    if iso_on and not hk_on:
        status = '\u26a0\ufe0f ISOLATED ONLY'
    elif iso_on and hk_on:
        status = '\u26a0\ufe0f SPLIT'
    else:
        status = '\u2713 housekeeping'
    cpustr = ','.join(str(c) for c in sorted(ec)) if ec else 'none'
    print('%-5s %-30s %8s %8s %-20s %-25s' % (irq, name[:30], aff, eff, cpustr, status))
