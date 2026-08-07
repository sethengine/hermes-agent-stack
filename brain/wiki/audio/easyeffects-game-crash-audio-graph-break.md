---
source_session: 20260805_194109_36b076
date: 2026-08-05
category: audio
tags: [easyeffects, pipewire, dota2, game-crash, audio-graph, no-sound]
related: [easyeffects-crash-missing-sink, easyeffects-pipewire-restart-crash, pipewire-alc1220-research-validated-config]
---

# Game Crash Breaks EasyEffects Audio Graph (No Sound)

A game crash (not an audio config fault) can cause sudden no-sound on the ALC1220 chain when EasyEffects is in the path.

**Cascade (observed Aug 5, Dota 2 segfault at 19:40:31):**
1. Game segfaults (SIGSEGV in `libclient.so`), its audio stream (`SDL Application`/`dota2` nodes) vanishes mid-flight
2. EasyEffects PipeWire manager loses the tracked resource → `pw_manager.cpp:148 Remote error ... unknown resource 260 op:2` error burst
3. WirePlumber: `WpSiStandardLink ... link failed: 1 of 1 PipeWire links failed to activate`
4. Audio routing through EasyEffects breaks → silence

**Diagnosis:** When "suddenly no sound" follows a frozen/crashed game, check whether the crash predates the silence. The graph is often healthy *now* (every link `active`, hardware sink RUNNING, ALSA Master `[on]`) because the graph re-stabilizes when the game is killed. A clean graph + hardware mixer on = not a mute/config fault — check the game crash first.

**Fix:** Kill the crashed game — the graph self-heals. No audio config change needed.

[[PipeWire ALC1220 validated config]]
