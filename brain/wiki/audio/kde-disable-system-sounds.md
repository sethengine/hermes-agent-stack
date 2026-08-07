---
category: audio
source_session: 20260607_135010_cab25e
date: 2026-07-21
tags: [kde, plasma, sound, audio, configuration]
---

# KDE System Sound Effects — Disable

KDE Plasma 6 plays GUI sound effects through the Oxygen system sound theme: volume slider feedback beeps, window maximize/minimize/close sounds, notification pops, error/warning dings.

## Quick Toggle

Set `Enable=false` under the `[Sounds]` section in `~/.config/kdeglobals`:

```ini
[Sounds]
Enable=false
```

## Apply Without Logout

Restart the Plasma shell to pick up the change immediately:

```bash
kquitapp6 plasmashell && sleep 2 && kstart6 plasmashell &
```

This flickers the desktop briefly; all windows and apps stay open.

## What's Affected

Disabled:
- Volume slider feedback beeps/clicks
- Window maximize/minimize/close sounds
- Notification pop sounds
- Error/warning dialog dings
- All other Oxygen theme GUI sound effects

Not affected:
- Media playback (music, video, browser audio)
- PipeWire/ALSA audio output
- Custom audio sinks ([[pipewire-alc1220-custom-sink]])

## Related

- [[pipewire-alc1220-custom-sink]]
- [[easyeffects-pipewire-restart-crash]]
