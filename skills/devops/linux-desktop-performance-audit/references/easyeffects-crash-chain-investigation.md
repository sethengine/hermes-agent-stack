# EasyEffects Crash Chain Investigation

## The Crash Cascade

When PipeWire or WirePlumber has unresolved errors (config syntax faults, device contention), EasyEffects crashes in a reproducible cascade:

```
PipeWire config error → front:1 contention → WirePlumber link failures
→ EE loses PipeWire node connections → EE auto-restarts
→ Tries to load pipeline from preset → corrupted INI-as-JSON preset
→ JSON parse error → SIGABRT (signal 6) → DrKonqi → coredump
→ systemd auto-restarts EE → repeat cycle
```

## Key Diagnostic Signals

### Signal 1: PipeWire Config Syntax Error
In `journalctl --user -u pipewire --since -1h`:
```
error in config '.../alsa-sink-alc1220.conf': Expected object key
```
**Root cause**: Unquoted string values in PipeWire SPA-JSON config (e.g., `resample.method = soxr` instead of proper syntax).

### Signal 2: ALSA Device Contention
```
spa.alsa: 'front:1': playback open failed: Device or resource busy
```
**Root cause**: Both the manual config sink AND WirePlumber's auto-detected sink try to open `front:1`. Only one succeeds. The other logs errors continuously.

### Signal 3: WirePlumber Link Failures
```
<WpSiStandardLink:0x...> link failed: 1 of 1 PipeWire links failed to activate
<WpSiStandardLink:0x...> link failed: some node was destroyed before the link was created
```
**Root cause**: PipeWire nodes being torn down while WirePlumber is still trying to link them → cascade of failed activations.

### Signal 4: Corrupted EE Preset
In `journalctl --user -u app-com.github.wwmm.easyeffects@*`:
```
presets_manager.cpp:441 parse error at line 1, column 2:
invalid literal; last read: '[G'
```
**Root cause**: File at `~/.local/share/easyeffects/output/*.json` that starts with `[General]` (INI format) but has a `.json` extension. EE reads it as JSON, fails at `[`, and ABRTs.

### Signal 5: Repeated EasyEffects Crashes
```
coredumpctl list easyeffects
```
Multiple coredumps with the same UUID hash → same crash repeated.

## Repair Sequence

1. **Remove corrupted preset**:
   ```
   rm ~/.local/share/easyeffects/output/max_quality.json
   ```
2. **Verify no other INI-as-JSON files**:
   ```
   find ~/.local/share/easyeffects -name '*.json' -exec sh -c 'head -c1 "$1" | grep -q "{" || echo "BAD: $1"' _ {} \;
   ```
3. **Fix PipeWire config syntax** — remove unquoted strings from `alsa-sink-alc1220.conf`
4. **Fix front:1 contention** — either use `hw:1` in the manual sink, or disable the WirePlumber auto-sink via `pactl suspend-sink`, or remove the manual sink entirely
5. **Restart stack**:
   ```
   systemctl --user restart pipewire wireplumber pipewire-pulse
   easyeffects --gapplication-service &
   ```
6. **Clean coredumps**:
   ```
   sudo rm -rf /var/lib/systemd/coredump/*
   ```

## Verification

```
journalctl --user -u pipewire --since -10m --no-pager | grep -i error
journalctl --user -u app-com.github.wwmm.easyeffects@* --since -10m --no-pager | grep -iE 'signal|error|abort'
pw-top -b -n 1 | awk '{print $NF, $(NF-1)}' | grep -v '0$' | grep -v 'FORMAT'
# ERR column should be 0 for all sinks
```

## Parallel Investigation Pattern

To gather all signals in one pass (no iterative back-and-forth):

```bash
# Batch 1 — hardware + kernel + services + pipewire
echo "=== CPU/LOAD ===" && cat /proc/loadavg
echo "=== TOP CPU ===" && ps aux --sort=-%cpu | head -10
echo "=== FAILED ===" && systemctl --failed
echo "=== SLOW BOOT ===" && systemd-analyze blame | head -10
echo "=== PW ERRORS ===" && journalctl --user -u pipewire --since -1h --no-pager | grep -i error | tail -20
echo "=== WP ERRORS ===" && journalctl --user -u wireplumber --since -1h --no-pager | grep -i fail | tail -20
echo "=== EE ERRORS ===" && journalctl --user -u app-com.github.wwmm.easyeffects@* --since -1h --no-pager | grep -iE 'signal|error|abort' | tail -20
echo "=== DMESG ===" && dmesg --level=err,warn 2>/dev/null | tail -10
echo "=== COREDUMPS ===" && sudo du -sh /var/lib/systemd/coredump/ 2>/dev/null
echo "=== WIFI POWERS ===" && iw dev 2>/dev/null | awk '/Interface/{print $2}' | while read i; do iw dev "$i" get power_save 2>/dev/null; done
```

The `echo "=== SECTION ===" && command` pattern lets every command run independently — one failure doesn't block the rest.
