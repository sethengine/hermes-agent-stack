# Error Transcripts — ALC1220 Audio Debugging

## 1. Intel Audio Card Not Detected

**dmesg/journactl:**
```
sof-audio-pci-intel-mtl 0000:80:1f.3: the DSP is not enabled on this platform, aborting probe
```

**aplay output before fix:**
```
card 0: NVidia [HDA NVidia] ...
```

**proc/asound/cards before fix:**
```
 0 [NVidia         ]: HDA-Intel - HDA NVidia
```

**lsmod (relevant):**
```
snd_sof_pci_intel_mtl
snd_sof_intel_hda_generic
snd_intel_dspcfg        (dsp_driver=3)
snd_hda_intel
```

**Current dsp_driver value:** `/sys/module/snd_intel_dspcfg/parameters/dsp_driver` = 1

## 2. PipeWire Startup Crash (status 234)

```
pipewire[690639]: mod.adapter: usage: node.name=<string>
pipewire[690639]: pw.resource: usage: node.name=<string>
pipewire[690639]: pw.conf: can't create object from factory adapter: Invalid argument
pipewire[690639]: default: failed to create context: Invalid argument
```

**Second attempt (GB206 config):**
```
pipewire[690647]: ALSA lib confmisc.c:165:(snd_config_get_card) Cannot get card index for 0
pipewire[690647]: spa.alsa: 'hw:0,3': playback open failed: No such file or directory
```

**Socket files unlinked after kill -9:** `/run/user/1000/pipewire-0` disappears but kernel still sees it in `/proc/net/unix`. Fix: `systemctl --user stop pipewire.socket` then restart.

## 3. Right Channel Silence

**amixer simple mixer (LIED):**
```
Simple mixer control 'Headphone',0
  Front Left: Playback 87 [100%] [0.00dB] [on]   <-- said this
  Front Right: Playback 87 [100%] [0.00dB] [on]   <-- said this
```

**Actual hardware state (via numid):**
```
numid=3,iface=MIXER,name='Headphone Playback Volume'
  : values=0,0                                     <-- was actually 0
numid=4,iface=MIXER,name='Headphone Playback Switch'
  : values=off,off                                 <-- was actually off
```

## 4. ALC1220 Codec Dump (relevant nodes)

```
Node 0x03 [Audio Output] — Headphone DAC
  Amp-Out vals:  [0x00 0x00]  (was muted)
  Converter: stream=1, channel=0
  Connection to 0x0d mixer → 0x1b (HP Out Front)

Node 0x02 [Audio Output] — Line Out DAC
  Amp-Out vals:  [0x46 0x46]  (working)
  Connection to 0x0c mixer → 0x14 (Line Out Rear)

Node 0x1b [Pin Complex] — Headphone jack
  Pin Default 0x02214020: [Jack] HP Out at Ext Front
  Pin-ctls: 0xc0: OUT HP VREF_HIZ
  Connection: 5 — 0x0c 0x0d* 0x0e 0x0f 0x26
```

## 5. EasyEffects Crash (SIGABRT)

```
Signal: 6 (ABRT)
Stack trace thread 2264 (crashing):
  #0  libc.so.6 + 0x9a29c
  #1  raise (libc.so.6)
  #2  abort (libc.so.6)
  #3  libQt6Core.so.6 + 0x98d3a
  #4  QDebug::~QDebug()  (libQt6Core.so.6)
  #5  /usr/bin/easyeffects + 0xfc988
  #6  /usr/bin/easyeffects + 0x6c55ba
  #7  libpipewire-module-protocol-native.so + 0xae4b
  #8  libspa-support.so + 0x69a6
  #9  libpipewire-0.3.so.0 + 0x8e201

Stack trace thread (LSP plugin - sleeping, not crashing):
  #3  lsp-plugins-lv2.so + 0x403512
  #4  clock_nanosleep (libc.so.6)
```

## 6. ALSA HW Params (working state)

```
access: MMAP_INTERLEAVED
format: S32_LE
subformat: STD
channels: 2
rate: 48000 (48000/1)
period_size: 512
buffer_size: 16384
```

## 7. PipeWire Node Params (working state)

```
channelVolumes: [0.551352, 0.551352]
channelMap: ["FL", "FR"]
softMute: false
format: S32LE
rate: 48000
channels: 2
position: ["FL", "FR"]
```

## 8. pw-top Format

```
S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME
S   31      0      0    ---     ---   ---   ---     0     S32LE 2 48000 alc1220-analog-sink
R  126   1024  48000  44,0us   3,1us  0,00  0,00    0     F32P 2 48000 easyeffects_sink
```
- `S` = SUSPENDED (not processing, can wake on demand)
- `R` = RUNNING (actively processing audio)
- `ERR` = cumulative error/underrun count on this node
- FORMAT column shows SPA naming (no underscore): `S32LE`, `F32P`, `F32LE`

## 9. Format Syntax Rules (from blow-ups)

| Location | Correct | Will Break |
|----------|---------|-----------|
| `adapter args` block | `audio.format = S32LE` | `"S32_LE"` (crashes PipeWire on startup) |
| `context.properties` | `default.audio.format = "S32_LE"` | Both forms work |
| `factory.name` value | `"api.alsa.pcm.sink"` (quoted) | `api.alsa.pcm.sink` (unquoted dots break parser) |
| `resample.quality` | `10` (integer) or `"soxr-vhq"` | Any invalid value |
| `node.suspend` | `false` (lowercase) | `False` or `"false"` |

## 10. context.exec Timing Trap

PipeWire processes config in this order:
1. `context.properties` (global settings)
2. `context.modules` (load modules)
3. `context.objects` (create adapter factories → opens ALSA hw:1 → codec resets)
4. `context.exec` (run commands)

If you put `amixer` in `context.exec`, it runs BEFORE the adapter opens the ALSA device. The amixer commands set the volume, then the adapter opens `hw:1` which reinitializes the codec → volume resets to 0. The fix is a retry script that keeps trying until the card is ready.

## 11. Volume Reset After Pause/Resume (idle→active transition)

Even with `node.suspend = false`, if PipeWire restarts the adapter reopens hw:1 and resets the codec. The retry script (`ensure-alc1220-volume.sh`) handles this by polling amixer until the values stick.

## 12. Node IDs (dynamic, reset on PipeWire restart)

Alc1220-analog-sink typically gets ID 31. EasyEffects nodes get IDs in the 100-200 range. These are NOT stable across restarts.
