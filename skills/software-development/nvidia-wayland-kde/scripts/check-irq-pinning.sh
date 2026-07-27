#!/bin/bash
# Quick diagnostic: verify IRQ pinning and C-state status
# Run after applying any pin-irqs-dynamic template.
# Exit codes: 0 = healthy, 1 = warnings (not fatal), 2 = errors found

echo "=== IRQ Distribution Check ==="

# Check NVIDIA IRQs
echo "--- GPU IRQs (should be on expected cores) ---"
grep -c "nvidia" /proc/interrupts > /dev/null 2>&1
if [ $? -eq 0 ]; then
    grep "nvidia" /proc/interrupts | while read line; do
        irq=$(echo "$line" | awk '{print $1}' | tr -d ':')
        shift=$(( $(echo "$line" | awk -F: '{print $1}' | wc -c) ))
        # Find which CPUs have hits
        hits=""
        for ((i=2; i<=21; i++)); do
            val=$(echo "$line" | awk -v n=$i '{print $n}')
            if [ -n "$val" ] && [ "$val" -gt 0 ] 2>/dev/null; then
                hits="$hits CPU$((i-2)):$val"
            fi
        done
        echo "  IRQ $irq →$hits"
    done
else
    echo "  No NVIDIA IRQs found"
fi

# Check USB IRQs
echo "--- USB IRQs (should be on expected cores) ---"
if grep -c "xhci_hcd" /proc/interrupts > /dev/null 2>&1; then
    grep "xhci_hcd" /proc/interrupts | while read line; do
        irq=$(echo "$line" | awk '{print $1}' | tr -d ':')
        hits=""
        for ((i=2; i<=21; i++)); do
            val=$(echo "$line" | awk -v n=$i '{print $n}')
            if [ -n "$val" ] && [ "$val" -gt 0 ] 2>/dev/null; then
                hits="$hits CPU$((i-2)):$val"
            fi
        done
        echo "  IRQ $irq →$hits"
    done
else
    echo "  No xHCI IRQs found"
fi

echo ""
echo "=== C-State Status (GPU+USB cores 8-13) ==="
errors=0
for cpu in 8 9 10 11 12 13; do
    echo -n "  CPU $cpu: "
    has_deep=0
    for s in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*/disable; do
        name=$(cat $(dirname "$s")/name 2>/dev/null)
        dis=$(cat "$s" 2>/dev/null)
        status="ON"
        [ "$dis" = "1" ] && status="DIS"
        echo -n "$name=$status "
        # Flag if C2 or C3 is still enabled on GPU+USB cores
        if [ "$name" = "C2_ACPI" ] && [ "$dis" != "1" ]; then has_deep=1; fi
        if [ "$name" = "C3_ACPI" ] && [ "$dis" != "1" ]; then has_deep=1; fi
    done
    if [ "$has_deep" = "1" ]; then
        echo " ⚠️  C2/C3 still enabled — may cause interrupt latency"
        errors=2
    else
        echo " ✓"
    fi
done

echo ""
echo "=== Governor Status (GPU+USB cores 8-13) ==="
for cpu in 8 9 10 11 12 13; do
    gov=$(cat /sys/devices/system/cpu/cpu$cpu/cpufreq/scaling_governor 2>/dev/null)
    echo -n "  CPU $cpu: $gov"
    if [ "$gov" != "performance" ]; then
        echo " ⚠️  should be 'performance'"
        errors=1
    else
        echo " ✓"
    fi
done

echo ""
echo "=== IRQ-concentrated core check ==="
# Warn if any single core handles >80% of all NVIDIA interrupts
nvidia_total=0
nvidia_max=0
nvidia_max_cpu=""
declare -a cpu_counts
for ((i=0; i<20; i++)); do cpu_counts[i]=0; done

while read line; do
    for ((i=2; i<=21; i++)); do
        val=$(echo "$line" | awk -v n=$i '{print $n}')
        if [ -n "$val" ] && [ "$val" -gt 0 ] 2>/dev/null; then
            cpu_idx=$((i-2))
            cpu_counts[$cpu_idx]=$((cpu_counts[$cpu_idx] + val))
            nvidia_total=$((nvidia_total + val))
        fi
    done
done < <(grep "nvidia" /proc/interrupts 2>/dev/null)

if [ "$nvidia_total" -gt 0 ]; then
    for ((i=0; i<20; i++)); do
        if [ "${cpu_counts[$i]}" -gt "$nvidia_max" ]; then
            nvidia_max=${cpu_counts[$i]}
            nvidia_max_cpu=$i
        fi
    done
    pct=$((nvidia_max * 100 / nvidia_total))
    if [ "$pct" -gt 80 ]; then
        echo "  ⚠️  CPU $nvidia_max_cpu handles ${pct}% of NVIDIA IRQs (${nvidia_max}/${nvidia_total})"
        echo "  This is a concentration risk. Consider spreading across more cores."
        errors=1
    else
        echo "  ✓ Best distributed: CPU $nvidia_max_cpu has max ${pct}% of ${nvidia_total} total IRQs"
    fi
fi

echo ""
if [ "$errors" = "0" ]; then
    echo "✓ All checks passed"
elif [ "$errors" = "1" ]; then
    echo "⚠️  Warnings found (non-critical)"
else
    echo "✗ ERRORS found — C2/C3 still enabled on IRQ cores"
fi

exit $errors
