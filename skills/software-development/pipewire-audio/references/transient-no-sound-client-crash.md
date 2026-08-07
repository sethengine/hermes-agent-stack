# "Suddenly No Sound" — Transient Client Crash Broke the EasyEffects Link Graph

## Symptom
User reports a sudden, total loss of audio. When you investigate, the PipeWire graph
may already look **healthy** — sinks RUNNING, no mute, all links `active`. This does
NOT mean the report was wrong: it means the fault was **transient** and self-healed.

## Root cause pattern
A single audio *client* crashed (game segfault, app killed, browser tab died) and took
down the links that route through it. With EasyEffects in the path, a client disappearing
mid-flight leaves EasyEffects' PipeWire manager tracking a stale resource. The SYNC of
symptoms in `journalctl`:

```
<game segfaults>  e.g. "SIGSEGV ... libclient.so"
easyeffects[pid]: pw_manager.cpp:148  Remote error res: No such file or directory
easyeffects[pid]: pw_manager.cpp:149  Remote error message: unknown resource 260 op:2
wireplumber: wp-event-dispatcher: <WpSiStandardLink...> link failed: 1 of 1 PipeWire links failed to activate
```

When you then hard-kill the frozen client, the graph re-stabilizes and sound returns.
So the freeze and the no-sound are usually the **same root cause** (the crash), not a
mute/hardware/config fault.

## Diagnosis order (read-only, no restarts)
1. **Confirm current health** — is the issue maybe already gone:
   ```bash
   wpctl status
   pactl get-default-sink
   pactl list short sinks
   wpctl get-volume @DEFAULT_AUDIO_SINK@    # no "MUTE" = not muted in graph
   ```
2. **Dump the FULL link graph** and confirm every hop reaches the physical sink. This is
   the decisive step — each EE plugin is a separate node and any broken hop = silence even
   when sinks show RUNNING:
   ```bash
   pw-dump 2>/dev/null | python3 -c "
   import sys,json
   d=json.load(sys.stdin)
   nm={s['id']:(s['info']['props'].get('node.name') or s['info']['props'].get('node.nick') or s['id']) for s in d if 'props' in s.get('info',{})}
   for s in d:
       if s.get('type')=='PipeWire:Interface:Link':
           i=s['info']; print(s['id'], i.get('state'), '|', nm.get(i.get('output-node-id')),'->',nm.get(i.get('input-node-id')))
   "
   ```
   Healthy EE output chain ends in: `... ee_soe_output_level -> alc1220-analog-sink` (active).
   Look for the final hop to the physical hardware sink by name. If all `active`, graph is sound.
3. **Rule out ALSA hardware mute** (this is a separate, persistent cause — see SKILL "ALC1220 right
   channel mute" / Master switch). PipeWire volume does NOT drive the kernel mixer:
   ```bash
   amixer -c1 sget Master; amixer -c1 sget PCM; amixer -c1 sget Headphone
   # Master = [on], PCM ~100%, Headphone [on] = hardware not muted
   ```
4. **Confirm the transient via journal timestamp correlation** between the client crash and
   the EasyEffects `unknown resource` / WirePlumber `link failed` errors:
   ```bash
   journalctl --since "-10 min" --no-pager | grep -iE "easyeffects|wireplumber|link failed|unknown resource"
   ```

## Conclusion
If the graph is healthy AND the hardware mixer is unmuted AND the journal shows the
"unknown resource / link failed" burst timestamp-matched to a killed/crashed client, the
answer is: **the crashing client broke the EE routing for a window; it self-healed.** No
config change needed. Recommend a per-app blocklist / isolating the crashing app rather
than a global mute hunt (see `references/easyeffects-game-audio-blocklist.md`).

## Caveats
- Do NOT restart PipeWire/WirePlumber just to "see if sound works" — you erase the evidence
  (journal correlation) and may trigger the EE SIGABRT chain-crash documented in SKILL.md.
- A genuinely persistent silence that does NOT correlate with a client crash is the ALSA-mixer
  or sink-vanished case — follow the SKILL's crash-recovery sequence instead.
- `pw-dump | python3` triggers Hermes' security scanner (pipe-to-interpreter). It's read-only and
  approvable; expect an approval prompt.