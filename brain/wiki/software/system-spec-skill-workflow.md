---
source: 20260712_173808_ec4e81
category: software
date: 2026-07-12
tags: [system-spec, skill, opencode, hardware, software, inventory, workflow]
---

# System-Spec Skill: Auto-Loaded HW/SW Inventory

A dedicated `system-spec` skill was created at `~/.hermes/skills/devops/system-spec/SKILL.md` capturing the full live-checked hardware and software specification of the workstation. Unlike static wiki docs, this skill is auto-loaded into every conversation when system details are relevant.

## What It Covers

- System overview (Manjaro, kernel 7.0.10, KDE 6.26 Wayland)
- Motherboard/BIOS (Gigabyte Z890 AERO G, BIOS F21)
- CPU (Ultra 7 265K, 20C/20T, 5.5 GHz)
- GPU (RTX 5060 Ti 16 GB, driver 595.71.05, CUDA 13.2)
- Memory (64 GiB DDR5-5600, 4×16 GB, 2048 hugepages)
- Storage (WD SN850X 2TB + Kingston 1TB)
- Display (HP X34 3440×1440 @ 165 Hz DP)
- Audio (ALC1220, PipeWire 1.6.5, EasyEffects)
- Input (Corsair Katar Pro XT + BY Tech Thor 230 via keyd)
- Network (Intel Wi-Fi 7 BE200)
- Kernel params (full GRUB cmdline)
- Software versions (Python, Node, Docker, CUDA, etc.)
- Quick verification commands to re-check any component

## How It Auto-Loads

Hermes scans skill descriptions at conversation start. The `system-spec` skill's description and tags trigger automatic loading for any system-related query (GPU, CPU, audio, display, kernel, gaming, etc.).

## Update Workflow

When hardware/software changes, run the quick verification commands in the skill, then use `skill_manage(action='patch', name='system-spec')` to update the relevant table.

## OpenCode Copy

A copy was written to `~/.config/opencode/skills/system-spec/SKILL.md` with simplified OpenCode-format frontmatter and Hermes-agnostic tool references. OpenCode auto-discovers and loads it on every turn.

## References
- [[manjaro-system-specs-arrow-lake]]
- [[system-latency-audit-findings]]
- [[linux-system-audit-skill-creation]]
