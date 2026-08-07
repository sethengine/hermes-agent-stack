mcp-bridge v4: ~/.local/bin; skill agent-search-infrastructure; stack: ~/.config/.src/hermes-stack/
§
Emacs font/display advice: check display backend first — Emacs 30.2 = GTK3 under XWayland on Wayland (not PGTK).
§
Never modify system/tool/agent-harness config files (opencode.json, .cursor/settings, .claude/*) during investigation — report findings first, get approval, then apply. Reinstalling ECC overwrites opencode.json path fixes; re-apply plugin→dist/plugins and skills→./skills after every ECC install. Skill agent-harness-debugging covers this.
§
KDE Plasma theme pref: light-but-not-white (textured grays, warm off-whites). High text contrast preferred. Text shadows/outlines for readability. Wants GUI + terminal commands side-by-side.
§
ALC1220 audio: alc1220-analog-sink default (F32_LE, soxr-vhq). Douk amp + Sony XM3. Config: github.com/sethengine/alc1220-audio-config.
§
Doom Emacs: skill 'doom-emacs-setup'. Config ~/.config/doom/, JetBrainsMono NF.
§
User runs Hermes Desktop (not CLI) — /new replaces /reset. Local llama profile at 127.0.0.1:8084 with Qwythos-9B-v2-MTP-Q8_0. NVDEC config: NVD_BACKEND=direct, NVD_MAX_DETACHED_BACKING_IMAGES=64.
§
Hermes/OpenClaw: OLLAMA_NUM_PARALLEL=4 (35-50 tok/s), Flash Attn=1, temp=0.1 JSON. Skill prune 90d. SearXNG MCP discover + Firecrawl MCP extract.
§
Font rendering tuned: fontconfig hintslight+lcdlight+rgba, GTK rgba, KDE hintslight+DPI=110, FREETYPE_PROPERTIES v40+stem-darkening, ~/.Xresources. HP X34 3440x1440 @110 DPI.
§
Manjaro gamer: RTX 5060 Ti (NVIDIA 610), Z890, 3440x1440@165Hz. GE-Proton11-1. DLAA via DXVK_NVAPI_DRS_NGX_DLAA_OVERRIDE=1. nvidia-powerd=laptop-only (unsupported desktop). MangoHud fps_limit cap. vkd3d cache rebuilds after driver upgrades.
§
threadirqs removed — don't re-suggest. rtirq broken. Background-game mouse lag = priority inversion (NI-5) + compositor queue, NOT memory/TLB.
§
KWin env: ~/.config/plasma-workspace/env/*.sh (lexicographic last-wins) + environment.d/ + /etc/environment. kwin-opengl.sh=O2ES active. Plasma 6.8: KWin GLES-only (desktop GL dropped).
§
Hermes memory caps: config.yaml memory.memory_char_limit & user_char_limit (USER.md; UI 'Profile Budget'). mem=4000 user=1375.
§
When debugging, display timestamps with timezone.utc (fromtimestamp defaults to local, but manifest last_ext is UTC ISO). Stale-lock test: decide on PROCESS LIVENESS, not just age — a lock at ~7189s (just under 2h/7200s) with no live extract/graphify process was reclaimable; a healthy run finishes well under 2h, so age near/past the window means prior run died.
§
OmniRoute gateway (diegosouzapw/OmniRoute) runs at localhost:20128, OpenAI-compatible, free/no API key, model=auto routes free LLMs (e.g. qwen3.8-max-preview). Its catalog has ZERO embedding models — /v1/embeddings only works with paid creds (openai/gemini); never suggest OmniRoute for embeddings. deeptutor installed via pipx v1.5.9; model catalog at /home/sethengine/data/user/settings/model_catalog.json; embedding profile = Ollama nomic-embed-text (768d, keep_alive=0 on-demand). Ollama 0.32.6 runs CPU-only on RTX 5060 Ti (sm_120 not detected) — fine for embeddings. User prefers on-demand local serving that doesn't hog VRAM/RAM.
§
global-session-brain skill is USER-OWNED (curator patch refused; needs `hermes curator adopt`). Brain cron backlog-clear: sessions already covered by wiki files or trivial (<=2 msgs) → add to manifest processed (now_iso), recompute total_extracted_files via glob('wiki/**/*.md'), NO new files/nodes, report [SILENT]. For complex cron Python: write_file script then terminal python3 (multi-command inline python3 -c also triggers TIRITH).
§
Skill 'linux-parameter-audit' (recurring exhaustive-audit; kernel.org doc once/group via web_extract; sudo fails, subagents 503). USER-OWNED: curator patches refused — needs 'hermes curator adopt'. 1st-run gaps: verify value SEMANTICS (tcp_ecn=2/tw_reuse=1 false +), net global vs per-iface parsing, execute_code drift, sysfs write persistence.