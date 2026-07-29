# Workstation + Desktop + Gaming Comprehensive Tune-Up (July 2026)

Full command reference for tuning a **Manjaro KDE Wayland · NVIDIA RTX 5060 Ti · Intel CPU** system.

---

## Layer 1 — Kernel & Scheduler

### linux-zen kernel (safe, good performance)
```bash
sudo pacman -S linux-zen linux-zen-headers
sudo update-grub
reboot
```

### CachyOS kernel (max performance — third-party repo, backup first)
```bash
git clone https://github.com/CachyOS/CachyOS-PKGBUILDS.git
cd CachyOS-PKGBUILDS
./install-cachyos-repo.sh
sudo pacman -Syu
sudo pacman -S linux-cachyos linux-cachyos-headers
sudo pacman -S scx scx-lavd cachyos-settings
sudo update-grub
reboot
```

### BPF scheduler — scx_lavd (best desktop + workstation balance)
```bash
sudo systemctl enable --now scx_lavd.service
# Verify: cat /sys/kernel/debug/sched_ext/root/ops  → should show scx_lavd
```

### Kernel params (/etc/default/grub, then `sudo update-grub`)
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash
  nvidia_drm.modeset=1 nvidia_drm.fbdev=0
  preempt=full nowatchdog
  snd_hda_intel.enable=0,1"
```

---

## Layer 2 — Memory & VM

```bash
sudo tee /etc/sysctl.d/99-performance.conf > /dev/null <<'EOF'
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.dirty_ratio = 30
vm.dirty_background_ratio = 5
kernel.numa_balancing=0
fs.file-max = 2097152
EOF
sudo sysctl --system
```

### ZRAM (compressed RAM swap)
```bash
sudo pacman -S zram-generator
sudo tee /etc/systemd/zram-generator.conf > /dev/null <<'EOF'
[zram0]
zram-size = ram / 2
compression-algorithm = zstd
swap-priority = 100
EOF
sudo systemctl start /dev/zram0
```

### Huge Pages
```bash
echo "vm.nr_hugepages = 512" | sudo tee -a /etc/sysctl.d/99-hugepages.conf
sudo sysctl -p /etc/sysctl.d/99-hugepages.conf
```

---

## Layer 3 — Storage & I/O

```bash
# NVMe I/O scheduler → none
echo none | sudo tee /sys/block/nvme0n1/queue/scheduler

# Make permanent via udev
sudo tee /etc/udev/rules.d/60-iosched.rules > /dev/null <<'EOF'
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
EOF

# Enable periodic TRIM
sudo systemctl enable --now fstrim.timer
```

### fstab — add `noatime,nodiratime` to root and home partitions
Edit `/etc/fstab` and add noatime to the options column for each ext4 partition.

---

## Layer 4 — KDE Compositor

```bash
# Backend settings
kwriteconfig6 --file kwinrc --group Compositing --key Backend OpenGL
kwriteconfig6 --file kwinrc --group Compositing --key GLCore true
kwriteconfig6 --file kwinrc --group Compositing --key AllowTearing true
kwriteconfig6 --file kwinrc --group Compositing --key UnredirectFullscreen true

# Disable heavy effects
for effect in Blur Wobbly Slide Fade Scale Glide Cover Cube; do
  kwriteconfig6 --file kwinrc --group "Effect-$effect" --key Enabled false
done

# Zero animation speed
kwriteconfig6 --file kdeglobals --group KDE --key AnimationSpeed 0

# VRR
kwriteconfig6 --file kwinrc --group Wayland --key AdaptiveSync true

# Apply
kwin_wayland --replace & disown
```

### Quick compositor toggle
```bash
# Suspend (gaming)
qdbus6 org.kde.KWin /Compositor org.kde.kwin.Compositor.suspend
# Resume
qdbus6 org.kde.KWin /Compositor org.kde.kwin.Compositor.resume
```

---

## Layer 5 — NVIDIA Compute & Workstation

```bash
# Persistence mode
sudo nvidia-smi -pm 1
sudo systemctl enable --now nvidia-persistenced

# Max performance
nvidia-settings -a "[gpu:0]/GpuPowerMizerMode=1"

# Monitor
nvidia-smi dmon -s pucvmet -d 1
```

### CUDA env vars (add to ~/.bashrc or /etc/environment)
```bash
CUDA_CACHE_DISABLE=0
CUDA_CACHE_MAXSIZE=4294967296
__GL_SHADER_CACHE=1
```

---

## Layer 6 — CPU Governor

```bash
# Auto-cpufreq (automatic governor switching)
sudo pacman -S auto-cpufreq
sudo systemctl enable --now auto-cpufreq

# Manual performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Energy performance preference
echo performance | sudo tee /sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference
# Available values: default performance balance_performance balance_power power
```

---

## Layer 7 — PipeWire Audio

```bash
mkdir -p ~/.config/pipewire/pipewire.conf.d
tee ~/.config/pipewire/pipewire.conf.d/99-low-latency.conf > /dev/null <<'EOF'
context.properties = {
    default.clock.rate = 48000
    default.clock.quantum = 512
    default.clock.min-quantum = 32
    default.clock.max-quantum = 2048
}
EOF
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### WirePlumber 0.5 — per-app quantum (e.g., Chrome)
Create `~/.config/wireplumber/wireplumber.conf.d/51-chrome-quantum.conf`:
```ini
monitor.audio.rules = [
  {
    matches = [ { application.name = "Google Chrome" } ]
    actions = { update-props = { node.quantum = 256 } }
  }
]
```
Then `systemctl --user restart wireplumber`.

### LACTD (GPU fan control) — reduce polling to avoid micro-stutters
```bash
sudo sed -i 's/interval_ms: 500/interval_ms: 2000/' /etc/lact/config.yaml
sudo sed -i 's/apply_settings_timer: 5/apply_settings_timer: 30/' /etc/lact/config.yaml
sudo systemctl restart lactd
``` audio xruns
```bash
pw-top  # Watch ERR column — should stay 0
```

---

## Layer 8 — Service Reduction

```bash
sudo systemctl mask bluetooth.service cups.service avahi-daemon.service ModemManager.service bolt.service 2>/dev/null
sudo systemctl disable --now power-profiles-daemon.service 2>/dev/null
sudo systemctl mask --user plasma-baloorunner.service 2>/dev/null
sudo journalctl --vacuum-size=200M
balooctl suspend && balooctl disable
sudo systemctl disable systemd-coredump.socket 2>/dev/null
```

---

## Layer 9 — Compiler & Build

```bash
# makepkg optimizations
sudo tee -a /etc/makepkg.conf > /dev/null <<'EOF'
MAKEFLAGS="-j$(nproc)"
COMPRESSZST=(zstd -c -T0 --ultra -20 -)
CFLAGS="-march=native -mtune=native -O3 -pipe -fno-plt"
CXXFLAGS="$CFLAGS"
RUSTFLAGS="-C target-cpu=native"
EOF

# ccache
sudo pacman -S ccache
```

### RAM-based build directory (if ≥ 32GB RAM)
```bash
sudo mkdir -p /tmp/build
echo "tmpfs /tmp/build tmpfs defaults,noatime,size=16G,mode=1777 0 0" | sudo tee -a /etc/fstab
sudo mount /tmp/build
```

---

## Gaming Stack

```bash
sudo pacman -S gamescope mangohud gamemode lib32-gamemode vulkan-tools
paru -S low-latency-layer-git protonup-qt
```

### Steam launch option template
```
gamemoderun mangohud gamescope --backend wayland -f --adaptive-sync --hdr --force-grab-cursor --rt -r <REFRESH> -- PROTON_ENABLE_NVAPI=1 %command%
```

### ⚠️ Dead Space Remake — NO low_latency_layer, NO PROTON_DLSS_UPGRADE
```
PROTON_ENABLE_NVAPI=1 gamemoderun mangohud %command%
```

### low_latency_layer — per-game only (not with Reflex-capable NVIDIA games)
```
# Install
paru -S low-latency-layer-git

# Verify
vulkaninfo | grep -A 5 low_latency

# Use only for games that benefit
VK_INSTANCE_LAYERS=VK_LAYER_low_latency_layer PROTON_ENABLE_NVAPI=1 DXVK_NVAPI_ALLOW_OTHER_DRIVERS=1 gamemoderun mangohud %command%
```

### DirectX Error / GPU Driver Crash — Diagnosis
If a Proton game shows "DirectX Error ... caused by the graphics driver crashing":
1. Strip ALL flags: `gamemoderun mangohud %command%`
2. Test — if stable, add flags back ONE AT A TIME
3. Most common cause: `VK_INSTANCE_LAYERS=VK_LAYER_low_latency_layer` conflicting with NVIDIA's native Reflex (`PROTON_ENABLE_NVAPI=1`)
4. Second most common: `PROTON_DLSS_UPGRADE=1` on non-CachyOS-Proton

---

## Quick Start — All in Order

```bash
# 1. Update
sudo pacman -Syu && reboot

# 2. NVIDIA open driver
sudo mhwd -i pci video-nvidia-open && reboot

# 3. Linux-zen kernel
sudo pacman -S linux-zen linux-zen-headers && sudo update-grub && reboot

# 4. Install everything
sudo pacman -S gamescope mangohud gamemode lib32-gamemode \
  auto-cpufreq zram-generator ccache fio btop stress \
  nvidia-settings vulkan-tools
paru -S low-latency-layer-git protonup-qt

# 5. Apply sysctl
sudo sysctl --system

# 6. KDE compositor (run all kwriteconfig6 commands from Layer 4)
kwin_wayland --replace & disown

# 7. PipeWire
mkdir -p ~/.config/pipewire/pipewire.conf.d
# (write 99-low-latency.conf from Layer 7)
systemctl --user restart pipewire pipewire-pulse wireplumber

# 8. CPU
sudo systemctl enable --now auto-cpufreq
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 9. NVIDIA compute
sudo nvidia-smi -pm 1
sudo systemctl enable --now nvidia-persistenced
nvidia-settings -a "[gpu:0]/GpuPowerMizerMode=1"

# 10. ZRAM
sudo systemctl start /dev/zram0

# 11. Trim services
balooctl suspend && balooctl disable
sudo systemctl mask bluetooth.service cups.service 2>/dev/null

# 12. GRUB
sudo update-grub && reboot
```
