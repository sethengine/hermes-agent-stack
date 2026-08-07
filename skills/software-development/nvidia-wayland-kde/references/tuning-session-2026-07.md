# Tuning Session — July 2026

Key learnings from a multi-session system tuning with Intel Ultra 7 265K + RTX 5060 Ti + KDE Wayland.

## scx_loader Dual Config Paths

The loader reads configs in this priority (highest first):
1. `/etc/scx_loader/config.toml` — **wins if present** (often missed)
2. `/etc/scx_loader.toml`
3. `~/.config/scx_loader.toml`
4. `/usr/share/scx_loader/config.toml` — package default, lowest priority

Editing /usr/share/ while /etc/ has a file = no effect.

## GameMode Overrides scx Scheduler

GameMode `[custom]` section can run `scxctl switch -s rusty` on game stop, overriding the scx_loader config every time a game exits. Check both:
```bash
grep -A2 "\[custom\]" /etc/gamemode.ini ~/.config/gamemode.ini
```

## EPP Locked by Performance Governor

With `intel_pstate=active` + `performance` governor (set at boot), EPP is locked with EBUSY. The workaround (temp switch to powersave, set EPP, switch back) doesn't always work because the governor is baked in at boot. Cosmetic only — performance governor + C2/C3 disabled already runs at max.

## IRQ Pinning + NVMe/iwiwifi Stragglers

NVMe and iwlwifi drivers reassign MSI-X queue affinity after `/proc/irq/` writes. Need a periodic timer (30-120s) to catch stragglers. The straggler catch pattern:

```bash
for irq in $(grep "nvme" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  cur=$(cat /proc/irq/$irq/smp_affinity 2>/dev/null)
  [ -n "$cur" ] && [ "$((16#${cur} & 0x3F00))" -ne 0 ] 2>/dev/null &&
    echo "fc000" > /proc/irq/$irq/smp_affinity 2>/dev/null
done
```

Same pattern for iwlwifi but with `& 0xFF` to catch P-core overlap.

## C-state Disable — `index` File Bug

On kernel 7.x, `/sys/devices/system/cpu/*/cpuidle/state*/index` does NOT exist. Scripts must extract the number from the directory name: `state_num="${dir##*state}"`. Using the non-existent `index` file causes all state checks to silently fail.

## Chrome flag conflicting patterns

- `--enable-features=X` and `--disable-features=X` cancel each other — Chrome uses disable as authoritiative
- `--enable-native-gpu-memory-buffers` causes rendering corruption on NVIDIA Wayland
- `--use-gl=angle` without `--use-angle=vulkan` may fall back to SwiftShader

## Watchdog defeats nohz_full

If `nohz_full=0-7` isolates P-cores but `watchdog_cpumask=0-19` remains default, the soft watchdog fires timer interrupts on isolated cores. Fix: add `watchdog_cpumask=8-19` to kernel cmdline.
