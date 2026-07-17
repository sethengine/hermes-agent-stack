#!/bin/bash
# CORRECT resume hook template
# Install: sudo cp this /usr/lib/systemd/system-sleep/latency-fix
# sudo chmod 755 /usr/lib/systemd/system-sleep/latency-fix
#
# $1 = pre|post (PHASE — which fires before/after sleep)
# $2 = suspend|hibernate|hybrid-sleep (TYPE of sleep)
# BUG FIX: case "$1" in post) — NOT case $2 in post) !!!

case "$1" in
    post)
        sleep 2
        
        # 1. Re-trigger USB input (re-apply hwdb MOUSE_POLL after xHCI resume error)
        udevadm trigger --subsystem-match=input 2>/dev/null || true
        udevadm trigger --subsystem-match=usb 2>/dev/null || true
        udevadm settle --timeout=3 2>/dev/null || true
        
        # 2. NVIDIA max performance (works on Wayland when called from user session)
        for d in :0 :1 :2; do
            nvidia-settings -a '[gpu:0]/GPUPowerMizerMode=1' -c "$d" 2>/dev/null || true
        done
        nvidia-smi -pm 1 2>/dev/null || true
        
        # 3. CPU performance governor (C-states locked via GRUB processor.max_cstate=1)
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo performance > "$cpu" 2>/dev/null || true
        done
        
        # 4. Re-apply sysctl (sleep can reset these)
        sysctl -w vm.swappiness=5 vm.dirty_ratio=5 vm.page-cluster=0 \
            kernel.sched_rt_runtime_us=-1 2>/dev/null || true
        
        # 5. Hugepages — compact first, then progressive allocate
        echo 1 > /proc/sys/vm/compact_memory 2>/dev/null || true
        sleep 1
        for pages in 512 1024 1536 2048; do
            echo "$pages" > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null
            sleep 0.5
            CURRENT=$(grep HugePages_Total /proc/meminfo | awk '{print $2}')
            [ "$CURRENT" = "$pages" ] && break || true
        done
        
        # 6. Restart KWin compositor (fixes NVIDIA modeset after resume)
        qdbus org.kde.KWin /Compositor suspend 2>/dev/null || true
        sleep 0.5
        qdbus org.kde.KWin /Compositor resume 2>/dev/null || true
        
        # 7. Ensure KWin compositing stays OFF (direct scanout)
        kwriteconfig5 --file /home/*/.config/kwinrc --group Compositing --key Enabled false 2>/dev/null || true
        
        # 8. Force display re-sync (fixes color range after sleep)
        kscreen-doctor output.DP-3.mode.3440x1440@165 2>/dev/null || true
        
        # 9. Log result
        HP=$(grep HugePages_Total /proc/meminfo | awk '{print $2}')
        logger "[latency-fix] Applied. HugePages=$HP"
    ;;
esac
