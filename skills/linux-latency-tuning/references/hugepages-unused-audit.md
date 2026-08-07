# Hugepages Allocation Audit — are 2048 pages (4GB) actually used? (2026-08)

## Conclusion: On this desktop they were UNUSED and got disabled (saved 4GB RAM)

`linux-latency-tuning`'s GRUB set had `hugepages=2048` (4GB) and its resume hook
re-allocated 2048 on every wake. Investigation proved ZERO consumers on a pure desktop
(no VM, no DB), so the allocation was pure waste and was removed.

## How to audit whether hugepages are genuinely used

Check consumption FIRST — not just that some pages are allocated:

```bash
grep HugePages_Total /proc/meminfo   # 2048 both → allocated
grep HugePages_Free /proc/meminfo    # 2048 free = nobody using them
grep -E 'HugePages_(Rsvd|Surp)' /proc/meminfo   # Rsvd=0 = nothing mapped at all

# per-process usage (any PID with Hugetlb kB > 0):
for sm in /proc/[0-9]*/smaps; do \
  awk -v p=$(echo $sm | cut -d/ -f3) '/Hugetlb/{h+=$2} END{ if(h+0>0) print p, h }' "$sm" 2>/dev/null; done

# any process with VmHugePages set:
grep -l 'VmHugePages' /proc/[0-9]*/status 2>/dev/null

# the usual consumers (all present AND active):
systemctl is-active libvirtd   # qemu/kvm guest → hugepage user
ps aux | grep -E 'qemu|kvm' | grep -v grep
```

A clean result looks like: `Total=Free`, `Rsvd=0`, no `Hugetlb`/`VmHugePages` lines, no
libvirtd. Those pages are doing nothing — only 4GB RAM reserved.

## Where hugepage allocators live (disable ALL of them)

```bash
grep -rniE "hugepages|nr_hugepages" \
  /etc/default/grub /etc/sysctl.d/ /etc/systemd/system/ \
  /etc/tmpfiles.d/ /etc/udev/rules.d/ /usr/lib/systemd/system-sleep/
```

Common allocator sources:
1. GRUB `GRUB_CMDLINE_LINUX_DEFAULT` → `hugepages</n>` (alloc at boot).
2. `/etc/sysctl.d/*` → `vm.nr_hugepages`.
3. A systemd oneshot `hugepages-alloc.service` writing `nr_hugepages`
   (`Before=local-fs.target`, `WantedBy=multi-user.target`). May be `disabled` but still
   present — remove the file + `daemon-reload`).
4. **system-sleep resume hook** — CRITICAL: a hook re-allocates 2048 every wakeup, so the
   live value reads 0 after a fresh boot but 2048 after suspend. Always grep hooks too.

Even if the live value is 0, the reserved entry appears as Total, you suspect a hook or
service will flip it back next wake.

## Free live pages

```bash
echo 0 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
# verify: grep HugePages_Total /proc/meminfo  → now 0
```

## When hugepages ARE worth keeping

Real consumers: QEMU/KVM guests, databases (PostgreSQL etc.), some large-audio/graphics
buffers. If present, keep the stepped allocation (512→1024→1536→2048). The loop MUST use
the `-ge 2048` guard (step: `[ "$CURRENT" -ge 2048 ] && break`), NOT `= $pages` which
breaks at 512 — a confirmed bug in the original resume hook.