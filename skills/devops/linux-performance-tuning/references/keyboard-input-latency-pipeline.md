# Keyboard Input Latency Pipeline — Investigation Reference

Full end-to-end latency path from keystroke to visible character on a Linux desktop (Wayland + NVIDIA + KDE). Includes every investigation command used in the June 2026 session.

## System Under Test

| Component | Detail |
|---|---|
| CPU | Intel Core Ultra 7 265K (Arrow Lake) — 8P+12E, no HT |
| GPU | NVIDIA RTX 5060 Ti (GB206), driver 595.71.05, nvidia-drm GBM |
| Display | KDE Plasma 6.6.5, Wayland, KWin 6.6.5, 3440x1440 @ 165Hz DP-3 |
| Terminal | Alacritty 0.17.0 (winit 0.30.13), native Wayland, GLES2 renderer |
| Keyboard | BY Tech Thor 230 (USB, vendor:product=331a:5020) |
| Kernel | 7.0.10-1-MANJARO, PREEMPT_DYNAMIC (preempt=full), CONFIG_HZ=1000 |

## Complete Investigation Command Sequence

These were the commands run in the actual investigation session, organized by layer.

### Hardware Baseline

```bash
# CPU + mem
cat /proc/cpuinfo | grep -m1 "model name"
free -h

# Display server
echo $XDG_SESSION_TYPE

# KWin version and compositor type
kwin_wayland --version
qdbus6 org.kde.KWin /Compositor org.freedesktop.DBus.Properties.Get \
  org.kde.kwin.Compositing compositingType
# → returned "gl2" (OpenGL 2 via EGL)

# KWin scheduling
chrt -p $(pidof kwin_wayland)
# → SCHED_RR | SCHED_RESET_ON_FORK, priority 1

# KWin compositor config
cat ~/.config/kwinrc | grep -A20 '\[Compositing\]'
# → LatencyPolicy=LatencyLow, AllowTearing=true, UnredirectFullscreen=true,
#   VrrPolicy=FullscreenOnly, AnimationSpeed=1

# KWin DRM backend check
env | grep -E 'KWIN_DRM|GBM_BACKEND'
# → KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1
# → KWIN_DRM_ALLOW_TEARING=1
# → GBM_BACKEND=nvidia-drm

# Monitor resolution + refresh
kscreen-doctor -o | grep "Modes:"
# → 3440x1440@165.00*  (current mode, 165Hz)
# Also check VRR: kscreen-doctor -o | grep Vrr
# → Vrr: Automatic (but not active for windowed apps)
```

### Kernel + Boot Config

```bash
# Active boot params
cat /proc/cmdline
# → preempt=full, nohz_full=0-7, rcu_nocbs=0-7, intel_iommu=on,igfx_off, iommu=pt
# → usbhid.kbpoll=1, usbhid.mousepoll=1

# Kernel preemption model
cat /sys/kernel/realtime 2>/dev/null || echo "not RT"
uname -a | grep -o "PREEMPT[^ ]*"
# → PREEMPT_DYNAMIC

# C-state configuration
cat /sys/module/intel_idle/parameters/max_cstate
# → 9 (allows package C9 — very deep sleep → 500-1000µs wake latency)

# Check scheduler tunables
sysctl kernel.sched_min_granularity_ns kernel.sched_wakeup_granularity_ns \
  kernel.sched_latency_ns
```

### IRQ Path Discovery

```bash
# Find USB controller IRQ (where keyboard lives)
grep xhci_hcd /proc/interrupts
# → IRQ 138: xhci_hcd on CPU13 (E-core!)
# → IRQ 130: xhci_hcd on CPU12 (E-core!)

# Find what CPU the USB IRQ is on
cat /proc/irq/138/smp_affinity_list
# → 13 (E-core — problem!)

# NVIDIA GPU IRQ distribution
grep nvidia /proc/interrupts
# → IRQ 146 on CPU8, IRQ 148 on CPU8+CPU10 (both E-cores)

# Check effective_affinity vs smp_affinity (differs for managed IRQs)
for irq in $(grep -E "nvidia|nvme|xhci_hcd" /proc/interrupts | awk '{print $1}' | tr -d ':'); do
  name=$(cat /proc/irq/$irq/actions 2>/dev/null || echo "unknown")
  aff=$(cat /proc/irq/$irq/smp_affinity 2>/dev/null || echo "N/A")
  eff=$(cat /proc/irq/$irq/effective_affinity 2>/dev/null || echo "N/A")
  echo "IRQ $irq ($name): configured=$aff effective=$eff"
done

# Critical cross-check: do USB and NVIDIA share a CPU?
grep -E "nvidia|xhci_hcd" /proc/interrupts | awk '{print $1, $(NF-1), $NF}'
```

### USB/HID Device Path

```bash
# Find keyboard USB devices
ls -la /dev/input/by-path/*-event-kbd

# Identify the specific keyboard
udevadm info /dev/input/by-path/pci-xxxx:xx:xx.x-usb-...-event-kbd | grep -E "ID_VENDOR|ID_MODEL|ID_INPUT"
# → BY Tech Thor 230 (vendor=331a, product=5020)

# USB HID descriptor (bInterval)
sudo lsusb -v -d 331a:5020 2>/dev/null | grep -E '(bInterval|HID Device|bInterfaceProtocol)'
# → bInterval=1 for keyboard interface (1ms polling — good)
# → HID bcdHID=1.11

# Kernel USB HID polling override
cat /sys/module/usbhid/parameters/kbpoll
# → 1 (already set to 1ms — from boot param usbhid.kbpoll=1)

# USB autosuspend on keyboard port
for dev in /sys/bus/usb/devices/*/product; do
  product=$(cat $dev 2>/dev/null)
  dir=$(dirname $dev)
  if [ -e "$dir/power/autosuspend" ]; then
    echo "$product: autosuspend=$(cat $dir/power/autosuspend)"
  fi
done
# → BY Tech Thor 230: autosuspend=2 (2s → suspend → 3-10ms resume!)
# → Corsair KATAR PRO XT: autosuspend=-1 (disabled — good)
```

### Alacritty-Specific Investigation

```bash
# Find Alacritty PID and check environment
ALC_PID=$(pgrep -x alacritty | head -1)
cat /proc/$ALC_PID/environ 2>/dev/null | tr '\0' '\n' | grep -E '^(WAYLAND|DISPLAY|WINIT)'
# → WAYLAND_DISPLAY=wayland-0 → native Wayland (not XWayland)
# → DISPLAY=:0 (both set — can use XWayland for fallback)

# Alacritty thread model
ps -T -p $ALC_PID
# Main thread handles both input and rendering
# Background threads: io event listener, smithay-clipboard, notify-rs, config watcher, PTY reader

# Alacritty scheduling
chrt -p $ALC_PID
# → SCHED_OTHER (normal), nice=0, runtime=2.8ms

# Alacritty renderer
strings /usr/bin/alacritty 2>/dev/null | grep -E 'gles|opengl|vulkan' | sort -u
# → GLES2 renderer (alacritty/src/renderer/text/gles2.rs)
# → OpenGL 3.3 context (#version 330 core)

# Alacritty version + winit backend
alacritty --version
# → 0.17.0 with winit 0.30.13

# Check if Alacritty has debug render timing
strings /usr/bin/alacritty 2>/dev/null | grep -E 'render_timer|prefer_egl' | sort -u
# → `render_timer` and `prefer_egl` are config keys in the debug section

# Alacritty Wayland FDs (to confirm native Wayland connection)
ls -la /proc/$ALC_PID/fd/ 2>/dev/null | grep wayland
# Should show a socket fd → /run/user/1000/wayland-0
```

## Specific Findings from This Session

### Finding 1: USB IRQ on E-core

USB controller (xhci_hcd, IRQ 138) was pinned to **CPU13 — an E-core**, not matching the stated "USB on P-cores 2-3" configuration.

Before fix: IRQ 138 on CPU13 (E-core, 4.6 GHz, worst wake latency)
After fix: IRQ 138 on CPU2 (P-core, 5.4 GHz, best wake latency)

Commands to verify and fix (one-shot):
```bash
# Check current
cat /proc/irq/138/smp_affinity_list

# Move to P-core 2 (one-shot, non-persistent)
echo 2 | sudo tee /proc/irq/138/smp_affinity_list
```

Permanent fix via systemd service:
```ini
# /etc/systemd/system/pin-usb-irq.service
[Unit]
Description=Pin USB keyboard IRQ to P-core 2
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 2 > /proc/irq/138/smp_affinity_list'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### Finding 2: USB Autosuspend on Keyboard

The BY Tech Thor 230 had `autosuspend=2` — every 2 seconds idle, the USB port suspends. Next keystroke waits 3-10ms for USB resume.

Permanent fix via udev rule:
```ini
# /etc/udev/rules.d/90-usb-input-noautosuspend.rules
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="331a", ATTRS{idProduct}=="5020", ATTR{power/autosuspend}="-1"
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", ATTRS{idProduct}=="1bac", ATTR{power/autosuspend}="-1"
```

### Finding 3: Deep C-states on IRQ Cores

`max_cstate=9` allowed package C9 sleep (1048µs wake latency). Combined with USB autosuspend, an idle-then-type cycle incurred both the USB resume delay AND the CPU wake delay.

Fix: `intel_idle.max_cstate=4` in kernel cmdline (blocks C6+, keeps C1 at 1µs, C2 at 127µs).

### Finding 4: Intel IOMMU Enabled

`intel_iommu=on` added DMA translation overhead to every GPU buffer exchange. On RTX 5060 Ti (Blackwell), this also triggers NVIDIA Xid 31 faults from NVDEC0 under Chrome video decode.

Fix: Remove `intel_iommu=on` from kernel cmdline entirely (no VM passthrough = no benefit).

### Finding 5: Alacritty at Normal Priority

Alacritty ran at SCHED_OTHER, nice=0 — competing equally with Chrome, Steam, and every other process. Under CPU load, input handling got delayed.

Fix: `nice -n -5` via modified `.desktop` desktop entry wrapper (for app-menu launch) or a systemd user service.

## The Complete Fix Sequence (as provided to the user)

```bash
# 1. USB IRQ → P-core (permanent systemd service)
sudo tee /etc/systemd/system/pin-usb-irq.service << 'EOF'
[Unit]
Description=Pin USB keyboard IRQ to P-core 2
After=sysinit.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo 2 > /proc/irq/138/smp_affinity_list'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now pin-usb-irq.service

# 2. Limit C-states (kernel cmdline)
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="intel_idle.max_cstate=4 /' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg
# OR for systemd-boot:
# sudo sed -i 's/^options/options intel_idle.max_cstate=4/' /boot/loader/entries/*.conf

# 3. USB autosuspend off for keyboard + mouse (udev rule)
sudo tee /etc/udev/rules.d/90-usb-input-noautosuspend.rules << 'EOF'
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="331a", ATTRS{idProduct}=="5020", ATTR{power/autosuspend}="-1"
ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1b1c", ATTRS{idProduct}=="1bac", ATTR{power/autosuspend}="-1"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger -v -s usb -a idVendor=331a

# 4. Remove Intel IOMMU (kernel cmdline)
sudo sed -i 's/ intel_iommu=on,igfx_off//g; s/intel_iommu=on,igfx_off //g; s/intel_iommu=on,igfx_off//g' /etc/default/grub
sudo grub-mkconfig -o /boot/grub/grub.cfg

# 5. Raise Alacritty priority (desktop file wrapper)
mkdir -p ~/.local/share/applications
cp /usr/share/applications/alacritty.desktop ~/.local/share/applications/
sed -i 's|^Exec=alacritty|Exec=sh -c "nice -n -5 alacritty"|' ~/.local/share/applications/alacritty.desktop
```

All five changes require a reboot (except the udev rule and desktop file which take effect on next trigger/launch).
