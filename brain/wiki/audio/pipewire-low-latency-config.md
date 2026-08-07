---
session: 20260502_150358_5e17d2
date: 2026-05-02
category: audio
tags: [pipewire, latency, audio, configuration, manjaro]
---

# PipeWire Low-Latency Configuration for Manjaro

PipeWire can be tuned for lower audio latency to prevent underruns and improve workstation responsiveness. Create `/etc/pipewire/pipewire.conf.d/10-lowlatency.conf`:

```
context.properties = {
    default.clock.rate = 48000
    default.clock.allowed-rates = [ 48000 ]
}
context.modules = [
    { name = libpipewire-module-protocol-native rate = 48000 }
    { name = libpipewire-module-adapter args = { clock.rate = 48000 } }
]
```

Apply with:
```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

Setting a fixed sample rate (48000) avoids resampling overhead. The default allowed-rates list is restricted to a single rate to eliminate rate-switching latency.

## References
- [[manjaro-system-specs-arrow-lake]]
