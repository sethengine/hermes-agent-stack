#!/bin/bash
# IRQ pinning: ALL IRQs → E-cores only, no overlap between GPU and USB
# Intel hybrid CPU (Arrow Lake / 265K): P-Cores 0-7, E-Cores 8-19
#
# E-cores 8-9:   GPU only           ← separate, dedicated
# E-cores 10-11:  USB only           ← separate, dedicated
# E-cores 12-19:  NVMe, audio, WiFi, ethernet
# P-cores 0-7:    untouched — reserved for game/foreground

# ADAPT the E-core ranges below if your CPU has a different layout.
# Verify with: cat /sys/devices/system/cpu/cpu*/topology/core_type

LOG="/var/log/irq-pinning.log"
echo "=== $(date) - IRQ Pinning (GPU/USB separate E-cores) ===" | tee -a "$LOG"

# 1. NVIDIA GPU → E-cores 8-9 only (never shared with USB)
i=8
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 8))  # E-cores 8-9
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "NVIDIA IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 2. USB xHCI → E-cores 10-11 only (never shared with GPU)
i=10
for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 10))  # E-cores 10-11
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "USB IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 3. NVMe → spread across E-cores 12-19
i=12
for irq in $(grep "nvme" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 8 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "NVMe IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 4. Audio → E-cores 12-19
for irq in $(grep "snd_hda_intel\|snd_sof\|snd_hda_codec" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 8 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "Audio IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 5. WiFi (iwlwifi) → E-cores 12-19
for irq in $(grep "iwlwifi" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 8 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "WiFi IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 6. Ethernet (igc) → E-cores 12-19 (pinned even if down; no-op when cable unplugged)
for irq in $(grep "igc\|enp129\|enp130" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 8 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "Ethernet IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# Optional: Lock GPU/USB E-cores to max performance
# Uncomment the next 3 lines if you want to prevent C3 sleep on IRQ cores
# cpupower -c 8-11 idle-set -D 2 >/dev/null 2>&1
# cpupower -c 8-11 frequency-set -g performance >/dev/null 2>&1
# echo "E-cores 8-11: max perf locked (no C3, governor=performance)" | tee -a "$LOG"

echo "Done — P-cores 0-7 free | GPU on E-cores 8-9 | USB on E-cores 10-11 | Rest on 12-19" | tee -a "$LOG"
