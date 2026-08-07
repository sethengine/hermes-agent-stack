# Native Game (Non-Proton) Input Lag Diagnosis

Diagnostic patterns for **native Linux games** (Source 2, Vulkan-native, or OpenGL-native) running via Steam Linux Runtime / pressure vessel. These patterns differ from Proton/DXVK/VKD3D titles in several important ways.

## Key Differences From Proton Gaming

| Area | Proton Game | Native Linux Game |
|------|------------|-------------------|
| Render API | DXVK/VKD3D translation layer | Direct Vulkan/OpenGL |
| CPU affinity | Proton sets via wine/Steam | **Pressure vessel** restricts CPUs |
| Env vars | `PROTON_ENABLE_WAYLAND=1`, `DXVK_*`, `VKD3D_*` | Game's own env vars, `SDL_*`, `__GL_*` |
| Thread patterns | Wine server threads, DXVK threads | Game engine threads (VKRenderThread, Async Pipeline, etc.) |
| Launch options | `PROTON_*` env vars | `-vulkan -high` render/path overrides |
| Wayland | Via XWayland (unless `PROTON_ENABLE_WAYLAND=1`) | Native Wayland or XWayland depending on SDL/GDK |

## Diagnosis Commands

### 1. GPU/CPU Utilization Imbalance

**The smoking gun:** GPU utilization << CPU utilization for a GPU-bound game engine.

```bash
# GPU state — utilization, clocks, power, PCIe link
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit,clocks.current.graphics,clocks.current.memory,pcie.link.gen.current,pcie.link.width.current --format=csv,noheader

# CPU load of the game process (PID from pgrep)
ps -p $(pgrep -x dota2 | head -1) -o pid,%cpu,%mem,rss,vsize,comm --no-headers
grep '^cpu ' /proc/stat; sleep 3; grep '^cpu ' /proc/stat

# Thread-level CPU breakdown (total game threads)
ls /proc/$(pgrep -x dota2 | head -1)/task/ | wc -l
```

**Interpretation:**
- GPU < 15% + CPU > 200% → render path likely wrong or game CPU-bottlenecked
- GPU < 15% + CPU < 200% → game is idle/paused/in menu
- GPU > 50% → render path OK, any lag is compositor/scheduling/input stack

### 2. Steam Linux Runtime / Pressure Vessel CPU Affinity

Steam runs native Linux games inside a `pressure-vessel` container that restricts CPU affinity — typically to P-cores only.

```bash
# Check game process CPU affinity
taskset -cp $(pgrep -x dota2 | head -1)

# Read the cgroup (confirms pressure vessel)
cat /proc/$(pgrep -x dota2 | head -1)/cgroup

# Game CPU mask in hex
cat /proc/$(pgrep -x dota2 | head -1)/status | grep Cpus_allowed

# If Cpus_allowed=000ff → restricted to CPUs 0-7 only
# Arrow Lake 265K: 0-7 = P-cores (8 cores from 20 total)
```

**What it means:** The game gets 8 P-cores but the other 12 E-cores are unavailable. The NVIDIA IRQs (CPUs 8-11) are on DIFFERENT cores than the game — this is actually correct. But with 87+ game threads on 8 cores, context switching pressure builds up.

### 3. Thread Priority Analysis

Check if game threads are running at degraded scheduling priority:

```bash
# Thread priority and policy for all game threads
for tid in /proc/$(pgrep -x dota2 | head -1)/task/*; do
  comm=$(cat $tid/comm 2>/dev/null)
  read stat < $tid/stat
  set -- $stat
  priority=$18
  nice=$19  
  policy=$41
  echo "$comm: priority=$priority nice=$nice policy=$policy"
done 2>/dev/null | sort -t: -k4
```

**Policy codes:** 0=SCHED_OTHER, 1=SCHED_FIFO, 2=SCHED_RR, 3=SCHED_BATCH, 4=SCHED_IDLE

**Key signals:**
- All threads at nice 0-12 (SCHED_OTHER) — game has no explicit priority boost
- Some VKRenderThread at SCHED_FIFO/RR — NVIDIA's Vulkan driver promoted them
- `Async Pipeline` threads at SCHED_RR (policy=2) — correct for continuous rendering work
- `Panorama Image` at nice=12 (SCHED_IDLE) — Source 2 UI thread at extremely low priority

**Normal Dota 2 thread naming patterns:**
- `VKRenderThread` — Vulkan rendering (many, one per stream)
- `Async Pipeline` — GPU command stream processing
- `AsyncTextureHoo` — Texture streaming
- `AudioMixer` — Audio mixing
- `Panorama Image` — Panorama UI image loading
- `Video Decode Th` — Replay/video playback
- `mangohud-nvidia`, `mangohud-hwinfo` — MangoHud injection
- `CSteamAudio*` — Steam Audio spatial audio
- `SDLPwAudio*` — PipeWire/SDL audio path
- `cuda-EvtHandlr` — CUDA event handling
- `VmaDefragThread` — Vulkan memory allocator defrag

### 4. Full IRQ Topology Dump

Map ALL hardware interrupts to their effective CPUs at a glance:

```bash
for irq in $(seq 1 300); do
  eff=$(cat /proc/irq/$irq/effective_affinity 2>/dev/null)
  [ -n "$eff" ] && printf "IRQ %3d: eff_affinity=%s\n" $irq $eff
done 2>/dev/null | sort -t: -k2
```

**Expected pattern on Arrow Lake 265K + NVIDIA:**
- CPU0: Legacy IRQs (timer, serial, RTC, ACPI) — unavoidable
- CPUs 8-11: NVIDIA GPU IRQs (properly spread via MSI-X)
- CPU12-13: USB xHCI (mouse/keyboard input)
- CPU14-19: NVMe, audio, WiFi, ethernet

**Check for overlap:** NVIDIA and USB should NOT share CPUs. If they do, GPU interrupt floods (100M+) delay USB input processing.

### 5. Dota 2 / Source 2 Launch Options

Add in Steam → Properties → Launch Options:

```
-vulkan -high -novid +@panorama_min_comp_layer_dimension 0 -prewarm_panorama
```

| Flag | Effect |
|------|--------|
| `-vulkan` | Forces Vulkan renderer explicitly (avoids auto-detect path) |
| `-high` | Elevates game process priority class |
| `-novid` | Skip intro video |
| `+@panorama_min_comp_layer_dimension 0` | Reduce Panorama UI compositing resolution floor |
| `-prewarm_panorama` | Pre-warm Panorama UI on startup |

On modern Dota 2 (2025+), `-vulkan` is the default — but explicitly passing it skips the auto-detection code path that might choose a suboptimal render mode.

### 6. KWin Compositor Gaming Settings

Check and fix settings that affect fullscreen gaming on Wayland:

```bash
# Check all relevant settings
kreadconfig5 --file kwinrc --group Compositing --key WindowsBlockCompositing
kreadconfig5 --file kwinrc --group Compositing --key AllowTearing
kreadconfig5 --file kwinrc --group Compositing --key VrrPolicy
kreadconfig5 --file kwinrc --group Compositing --key LatencyPolicy
kreadconfig5 --file kwinrc --group Compositing --key MaxFps
kreadconfig5 --file kwinrc --group Compositing --key AnimationSpeed

# Optimal gaming values:
# WindowsBlockCompositing=true  — suspend compositing for fullscreen windows
# AllowTearing=true             — allow tearing when beneficial
# VrrPolicy=2                   — always-on VRR (2=Always, 1=FullscreenOnly)
# LatencyPolicy=LatencyLow      — prioritize latency over throughput
```

### 7. Memory Pressure Diagnosis

Memory pressure affects game responsiveness via zram swap + page compression:

```bash
# Memory overview
free -h

# Zram swap usage
zramctl

# Per-process memory (top consumers)
ps aux --sort=-%mem | head -10

# Page fault counters for game process
grep -E '^(pgfault|pgmajfault)' /proc/$(pgrep -x dota2 | head -1)/status

# Check if swappiness is active
sysctl vm.swappiness
```

**When to act:** Swap > 1GB on zram during gaming, or major page faults > 100/s on the game process.

### 8. EasyEffects / Audio Blocklist

EasyEffects DSP chain adds audio processing latency that can make the feel laggy:

```bash
# Check if game audio goes through DSP
grep -i "dota\|steam\|game" /home/*/.config/easyeffects/blocklist.json 2>/dev/null

# Check PipeWire quantum (lower = less latency)
pw-metadata -n settings | grep quantum

# PipeWire forced quantum
grep force-quantum ~/.config/pipewire/pipewire.conf.d/*.conf 2>/dev/null
```

Fix for native games: Add `dota2`, `steam`, `steamwebhelper` to EasyEffects blocklist.

### 9. NVIDIA Wayland Env Verification

```bash
# What KWin actually inherited
cat /proc/$(pgrep kwin_wayland | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep -E 'KWIN_DRM|__GL|WLR'

# What the session loaded
systemctl --user show-environment 2>/dev/null | grep -E 'KWIN_DRM|__GL'

# Key env vars for gaming:
# KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1  (KDE6 — reduces swapchain latency)
# KWIN_DRM_ALLOW_TEARING=1
# __GL_SYNC_TO_VBLANK=0                (no forced VSync)
# __GL_MaxFramesAllowed=1              (limit GPU queued frames)
# __GL_VRR_ALLOWED=1                   (allow VRR even without VSync)
```

### 10. PipeWire Quantum Under Gaming

```bash
# Current state
pw-metadata -n settings | grep quantum

# Config layers (check ALL for conflicts)
grep -rn 'quantum\|period-size\|force.quantum' ~/.config/pipewire/ /etc/pipewire/ 2>/dev/null | grep -v '^\s*#'

# Recommended gaming values:
# force-quantum=64 or 128 (1.3ms or 2.6ms at 48kHz)
# Default 256 (5.3ms) is fine for desktop, high for competitive
```

## Example: Full Dota 2 One-Shot Diagnosis

Run this while Dota 2 is running (in game, not main menu):

```bash
PGID=$(pgrep -x dota2 | head -1)
echo "=== GPU UTIL ==="
nvidia-smi --query-gpu=utilization.gpu,power.draw,clocks.current.graphics --format=csv,noheader
echo "=== CPU UTIL ==="
ps -p $PGID -o %cpu,%mem,rss --no-headers
echo "=== CPU AFFINITY ==="
taskset -cp $PGID
echo "=== THREAD COUNT ==="
ls /proc/$PGID/task/ | wc -l
echo "=== THREAD PRIORITIES ==="
for tid in /proc/$PGID/task/*; do
  comm=$(cat $tid/comm 2>/dev/null)
  read stat < $tid/stat
  set -- $stat
  echo "$comm: nice=$19 policy=$41"
done 2>/dev/null | sort | uniq -c | sort -rn
echo "=== MEMORY PRESSURE ==="
grep -E '^(pgfault|pgmajfault)' /proc/$PGID/status
free -h
zramctl
echo "=== KWIN SETTINGS ==="
kreadconfig5 --file kwinrc --group Compositing --key WindowsBlockCompositing
kreadconfig5 --file kwinrc --group Compositing --key AllowTearing
kreadconfig5 --file kwinrc --group Compositing --key VrrPolicy
kreadconfig5 --file kwinrc --group Compositing --key LatencyPolicy
```

## Pitfalls

- **Native game ≠ Proton game**: Don't suggest `PROTON_ENABLE_WAYLAND`, `DXVK_*`, or `VKD3D_*` env vars for native titles. They use `SDL_*`, `__GL_*`, and game-specific flags.
- **Pressure vessel CPU affinity**: `Cpus_allowed=000ff` (8 cores) is intentional by Steam. Not a bug. Don't suggest widening it with `taskset` unless you know the game has >8 hot threads.
- **GPU utilization in menus/splash**: Games that are loading or paused show low GPU. Only diagnose GPU utilization during active gameplay.
- **MangoHud adds CPU overhead**: The `LD_PRELOAD` shim runs on every frame. On a CPU-bottlenecked game, MangoHud itself adds measurable latency. Test with MangoHud disabled.
- **KWin `WindowsBlockCompositing=true`**: On Wayland this doesn't fully disable compositing like it did on X11. It signals KWin to minimize overhead. Still worth setting.
- **PipeWire force-quantum < 128**: May cause xruns/crackles on complex DSP chains (EasyEffects). Step down gradually: 256 → 128 → 64.
