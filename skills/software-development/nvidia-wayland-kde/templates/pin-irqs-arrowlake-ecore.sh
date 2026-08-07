#!/bin/bash
# pin-irqs-arrowlake-ecore v4
# Intel 265K Hybrid: P-cores 0-7 (5.4GHz) | E-cores 8-19 (4.6GHz)
#
# Cores 8-11: NVIDIA GPU IRQs only (round-robin across 4 cores)
# Cores 12-13: USB xHCI IRQs only (round-robin across 2 cores)
# Cores 14-19: Best-effort for NVMe/audio/WiFi/ethernet
# P-cores 0-7: Untouched — reserved for game/foreground apps
#
# GPU+USB E-cores: C2/C3 disabled, perf governor, EPP=performance
#
# Installation:
#   sudo cp this-file /usr/local/bin/pin-irqs-dynamic
#   sudo chmod +x /usr/local/bin/pin-irqs-dynamic
#   sudo systemctl restart pin-irqs-dynamic
#
# Verify:
#   grep "nvidia\|xhci" /proc/interrupts | awk '{printf "IRQ %s → ", $1; for(i=2;i<=21;i++) if($i>0) printf "CPU%d:%d ", i-2, $i; print ""}'
#   # GPU IRQs on E-cores 8-11, USB on 12-13
#   # C2 and C3 should be DISabled on cores 8-13
#   for cpu in 8 9 10 11 12 13; do echo -n "CPU $cpu: "; for s in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*/disable; do name=$(cat $(dirname $s)/name 2>/dev/null); dis=$(cat $s 2>/dev/null); echo -n "$name=$( [ "$dis" = 1 ] && echo DIS || echo ON ) "; done; echo; done

LOG="/var/log/irq-pinning.log"
echo "=== $(date) - IRQ Pinning v4 (GPU on E-cores 8-11, USB on E-cores 12-13, C2/C3 off, EPP=perf) ===" | tee -a "$LOG"

# ---------------------------------------------------------------
# STEP 1: GPU + USB E-cores → max performance
# ---------------------------------------------------------------
PERF_CORES="8 9 10 11 12 13"

for cpu in $PERF_CORES; do
    cpupath="/sys/devices/system/cpu/cpu$cpu"

    # Disable C2 (127us) and C3 (1048us) — keep only POLL and C1 (1us)
    # NOTE: Use ${state_dir##*state} to extract index from dir name.
    # The 'index' file does NOT exist in cpuidle on kernel 7.x
    # (cat "$state_dir"/index returns empty → -ge check silently skips).
    for state_dir in "$cpupath"/cpuidle/state*; do
        [ -d "$state_dir" ] || continue
        state_name=$(cat "$state_dir"/name 2>/dev/null)
        state_num="${state_dir##*state}"
        if [ "$state_num" -ge 2 ] 2>/dev/null; then
            echo 1 > "$state_dir"/disable 2>/dev/null
            echo "  CPU $cpu: disabled $state_name (state $state_num)" | tee -a "$LOG"
        fi
    done

    # EPP first (governor may lock it), then performance governor
    # cpupower works around the sysfs lock when performance governor is active
    cpupower -c "$cpu" set --epp performance >/dev/null 2>&1
    echo "performance" > "$cpupath"/cpufreq/scaling_governor 2>/dev/null
done

# ---------------------------------------------------------------
# STEP 2: NVIDIA GPU → E-cores 8-11
# ---------------------------------------------------------------
i=0
for irq in $(grep "nvidia" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 4 + 8))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "GPU IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# ---------------------------------------------------------------
# STEP 3: USB xHCI → E-cores 12-13
# ---------------------------------------------------------------
i=0
for irq in $(grep "xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    core=$((i % 2 + 12))
    echo "$core" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    echo "USB IRQ $irq → CPU $core" | tee -a "$LOG"
    ((i++))
done

# ---------------------------------------------------------------
# STEP 4: Background IRQs (NVMe/WiFi/audio/eth) → E-cores 14-19
# ---------------------------------------------------------------
# Hex mask: bits 14-19 = 0xFC000.  Use smp_affinity (hex mask)
# rather than smp_affinity_list for ranges.
MASK_14_19="fc000"

for irq in $(grep -E "nvme|iwlwifi|igc|enp129|enp130|snd_hda_intel|snd_sof" /proc/interrupts | \
    awk '{print $1}' | tr -d ':'); do
    echo "$MASK_14_19" > /proc/irq/$irq/smp_affinity 2>/dev/null
    echo "Background IRQ $irq → mask 14-19" | tee -a "$LOG"
done

# ---------------------------------------------------------------
# STEP 5: Catch stragglers — re-pin NVMe queues that escaped to 8-13
# ---------------------------------------------------------------
# NVMe driver may override affinity on its MSI-X queues.
# This check catches queues that drifted onto GPU/USB cores.
for irq in $(grep "nvme" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
    current_mask=$(cat /proc/irq/$irq/smp_affinity 2>/dev/null)
    if [ -n "$current_mask" ]; then
        dec_mask=$((16#${current_mask}))
        overlap=$((dec_mask & 0x3F00))  # bits 8-13 = GPU+USB zone
        if [ "$overlap" -ne 0 ] 2>/dev/null; then
            echo "$MASK_14_19" > /proc/irq/$irq/smp_affinity 2>/dev/null
            echo "STRAggLER: NVMe IRQ $irq was on CPU 8-13 zone, moved to 14-19" | tee -a "$LOG"
        fi
    fi
done

echo "Done — GPU on 8-11 | USB on 12-13 | C2/C3 off on 8-13 | EPP=perf on 8-13 | Background on 14-19" | tee -a "$LOG"
