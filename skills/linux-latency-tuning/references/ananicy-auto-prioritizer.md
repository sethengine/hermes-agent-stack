# ananicy-cpp — the silent auto-nice daemon

## What it is
**ANother Auto NIce daemon (C++ edition)** — a background agent that continuously
adjusts the `nice`/`ionice`/scheduling class of running processes from a 15k-row
ruleset. It re-ranks processes autonomously, so it's the usual source of "why does
random app X have high prio in htop?" — the user never set it.

- Unit: `ananicy-cpp.service` (runs itself at `Nice=-5`).
- Config root: `/etc/ananicy.d/` → `ananicy.conf` (feature toggles + `check_freq`,
  default 15s), `00-types.types` (the type→nice map), `00-default/` (per-process
  name rules). Type map is also shipped in `/usr/share/ananicy/ananicy.conf`
  on Arch.
- Rules: thousands of `{ "name": "<process>", "type": "<Type>" }` entries grouped
  in `00-default/<category>/*.rules`. `grep -rhE '"type"' ... | uniq -c` shows the
  distribution (e.g. Game×13k, BG_CPUIO×1.5k).

## The type → nice hierarchy (from 00-types.types)
THE CORE LOOKUP — this defines who gets boosted above whom:
| Type            | nice  | ioclass / notes                      |
|-----------------|-------|--------------------------------------|
| LowLatency_RT   | -12   | best-effort (wireguard, corectrl_helper) |
| Game            | -5    | best-effort (13k rule matches!)      |
| Player-Audio/Video, Image-View, Doc-View | -4 | Player-Audio has ionice RT sometimes |
| Chat            | -3    | best-effort, ionice 7                |
| IN_DIFF         | 0     | (default, unclassified)              |
| Heavy_CPU       | 9     | best-effort, ionice 7                |
| Service         | 10    | best-effort, ionice 6                |
| BG_CPU / Launcher | 14/16 | idle ioclass                        |
| BG_CPUIO        | 16    | idle ioclass, sched idle             |

## The pitfall this session hit (Chris' case)
Hermes desktop UI got bumped to `nice -8` and the compositor/audio (KWin,
pipewire, plasmashell) were NOT managed by ananicy at all — they set their OWN
priority at launch (`kwin_wayland=-12 SCHED_RR`, `pipewire=-12 TS`, `keyd=-12 FF`,
`plasmashell=-6`). So ananicy, by promoting a Game/Electron/UI app to -5/-8,
could push an ARBITRARY userspace app ABOVE plasmashell (-6) and near KWin (-12).
That silently inverts the intended priority hierarchy and reproduces the very
jank/stutter the tuning is trying to kill.

Key insights:
- IRQs that matter (xhci USB = 131/139, nvidia GPU = 147-154) are ALREADY
  SCHED_FIFO threaded IRQs — kernel-top priority by design. Nothing hijacks them.
- The desktop shell/audio is ALREADY the top userspace tier. Do not blindly
  re-nice stuff; first find WHO set the current value.
- ananicy-cpp is a black box overriding explicit manual tuning — for a user who
  hand-tools IRQ/tuning, it fights intent (a `renice` you do is undone on the next
  15s scan).

## Diagnose "why is X high prio in htop"
```
# Who set the nice value?
systemctl is-active ananicy-cpp   # if active, it likely did
ps -eo pid,comm,ni,cls | grep -E 'kwin|pipewire|plasmashell|Hermes|keyd'
cat /etc/ananicy.d/00-types.types         # the type->nice map
grep -rniE 'hermes|electron|chat' /etc/ananicy.d/00-default/ 2>/dev/null
```
Note precedence: kernel-hard IRQ threads and the desktop shell are self-set high;
anicy fills the rest.

## Fixes
Option A — full manual control (fits a hand-tuned latency box):
```
sudo systemctl disable --now ananicy-cpp.service
```
All `nice` fall back to defaults; your governor/HWP/IRQ-pin tuning still governs.
Nothing breaks — no service depends on it.

Option B — keep it but stop it from touching your stack: add a custom rule pinning
the protected processes to their preferred type/nice in `/etc/ananicy.d/`.
Fiddlier; ananicy still scans and can override other PIDs.

Option C — explicit enforcement guard (band-aid for "must-stay-high items"):
a systemd unit / resume-hook step that re-asserts the top tier:
```
for p in kwin_wayland pipewire wireplumber keyd; do pid=$(pgrep -x "$p"|head -1);
  [ -n "$pid" ] && { chrt -r -p 41 "$pid" 2>/dev/null; renice -n -12 -p "$pid"; }; done
```
plus a safety cap demoting any process with nice < -11 not in the trusted set
down to -10 so a stray Game can never preempt the compositor. (chrt -r on
pipewire is standard pro-audio; only do it if the binary is designed for RT.)

## Verify / read the current top tier
```
ps -eo pid,comm,ni,cls | sort -k3 -nr | head   # cls TS/RR/FF
cat /proc/$(pgrep -x kwin_wayland|head -1)/stat | awk '{print $19}'  # nice
echo $(cat /proc/irq/147/actions) /proc/irq/147/priority
# IRQ priority note: threaded IRQs (irq/147-nvidia) show as FF under cls.
```