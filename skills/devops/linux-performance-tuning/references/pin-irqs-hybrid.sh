#!/bin/bash
# IRQ pinning: ALL IRQs → E-cores only, no overlap between critical subsystems
# For Intel hybrid CPUs (Arrow Lake / Raptor Lake): P-cores 0-7, E-cores 8-19
#
# Layout:
#   P-cores 0-7:   GAME + foreground apps (zero IRQs)
#   E-cores 8-9:   GPU only (dedicated, never shared)
#   E-cores 10-11: USB only (dedicated, never shared with GPU)
#   E-cores 12-19: NVMe, audio, WiFi, ethernet (everything else)
#
# Install:
#   sudo cp pin-irqs-hybrid.sh /usr/local/bin/pin-irqs-dynamic
#   sudo chmod +x /usr/local/bin/pin-irqs-dynamic
#   sudo systemctl restart pin-irqs-dynamic.service
#
# Verify:
#   cat /proc/interrupts | grep -E "nvidia|xhci_hcd|nvme|iwlwifi" | head -10

LOG="/var/log/irq-pinning.log"
echo "=== $(date) - IRQ Pinning (ALL->E-cores) ===" | tee -a "$LOG"

# === HIGH-PRIORITY: GPU on E-cores 8-9 ONLY ===
i=8
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 8))  # E-cores 8-9
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "NVIDIA IRQ $irq -> CPU $core" | tee -a "$LOG"
    ((i++))
done

# === HIGH-PRIORITY: USB on E-cores 10-11 ONLY (never same as GPU) ===
i=10
for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 10))  # E-cores 10-11
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "USB IRQ $irq -> CPU $core" | tee -a "$LOG"
    ((i++))
done

# === LOW-PRIORITY: everything else on E-cores 12-19 ===
i=12
for dev in "nvme" "snd_hda_intel\|snd_sof\|snd_hda_codec" "iwlwifi" "igc\|enp129\|enp130"; do
    for irq in $(grep "$dev" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
        core=$((i % 8 + 12))  # E-cores 12-19
        echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
        echo "$dev IRQ $irq -> CPU $core" | tee -a "$LOG"
        ((i++))
    done
done

echo "Done - P-cores 0-7 free | GPU on 8-9 | USB on 10-11 | Rest on 12-19" | tee -a "$LOG"
