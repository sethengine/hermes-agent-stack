#!/bin/bash
# IRQ pinning: GPU + USB → P-cores, background → E-cores
# Intel 265K P-Cores: 0-7 | E-Cores: 8-19
#
# P-cores 0-1:   GPU only           ← fast cores for display
# P-cores 2-3:   USB only           ← fast cores for input
# E-cores 12-19: NVMe, audio, WiFi, ethernet
# P-cores 4-7:   untouched          ← reserved for foreground apps
#
# Installation:
#   sudo cp this-file /usr/local/bin/pin-irqs-dynamic
#   sudo chmod +x /usr/local/bin/pin-irqs-dynamic
#   sudo systemctl restart pin-irqs-dynamic
#
# Verify:
#   grep "nvidia" /proc/interrupts | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10}'
#   # Expect nvidia IRQs on CPU0/CPU1 (P-cores 0-1), NOT on CPU8/CPU9 (E-cores)

LOG="/var/log/irq-pinning.log"
echo "=== $(date) - IRQ Pinning (GPU/USB on P-cores) ===" | tee -a "$LOG"

# 1. NVIDIA GPU → P-cores 0-1 only (fast IRQ handling)
i=0
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2))  # P-cores 0-1
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "NVIDIA IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# 2. USB xHCI → P-cores 2-3 (fast input handling)
i=2
for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 2))  # P-cores 2-3
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

# 6. Ethernet (igc) → E-cores 12-19
for irq in $(grep "igc\|enp129\|enp130" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 8 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "Ethernet IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

echo "Done — GPU on P-cores 0-1 | USB on P-cores 2-3 | Rest on E-cores 12-19 | P-cores 4-7 free" | tee -a "$LOG"
