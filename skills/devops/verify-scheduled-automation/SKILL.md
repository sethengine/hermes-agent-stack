---
name: verify-scheduled-automation
description: Verify scheduled automation actually runs.
user-invocable: true
---

# Verify Scheduled Automation

When asked "does X run properly?" where X is a cron job, systemd timer, or git-backed backup, do NOT trust the skill/config that documents it. Verify the LIVE dispatch against reality. A skill or config can claim one mechanism (e.g. "Hermes cron job") while the real scheduler that fires is a completely different layer.

## The dispatch layers that can run an automation

Check ALL of these — more than one may apply, and the documented one may not be the live one:

| Layer | Where configured | How to check |
|---|---|---|
| Hermes cron | `~/.hermes/cron/jobs.json` | `grep -o '"name":"[^"]*"' ~/.hermes/cron/jobs.json \| grep -i <name>` |
| User systemd timer/service | `~/.config/systemd/user/*.{service,timer}` | `systemctl --user is-enabled <timer>`, `systemctl --user is-active <timer>` |
| System systemd timer/service | `/etc/systemd/system/*.{service,timer}` | `systemctl list-units` / `list-timers` |
| User crontab | `crontab -l` | `crontab -l \| grep <name>` |
| Chain (a stack-sync skill shells into another backup.sh) | arbitrary | trace the ExecStart / script calls |

## Proving a run actually happened (not just "configured")

Configuration is NOT execution. Get real evidence:

- **Timer last fire**: `systemctl --user list-timers <name>.timer` — read `LAST` and `PASSED` (and `NEXT`). Don't stop at `is-enabled`; an enabled timer can still never have fired.
- **Commit fate**: `git -C <repo> log --oneline --date=iso -5` and compare commit times to the schedule (a daily backup shows one commit per day at the scheduled time).
- **ExecStart → current script?**: `cat ~/.config/systemd/user/<service>` — confirm `ExecStart=%h/.dotfiles/backup.sh` (or equivalent) targets the live script, not a stale path.
- **Deployed script has the new code?**: `grep -c <marker_fn> <script>` — if you added a new function (e.g. `sync_system_files`), the live copy must contain it. A config can be current in the repo but stale on disk.
- **Clean run now**: `bash <script> 2>&1; echo "exit: $?"` — a 0 exit exercises the body incl. system-sync + secret redaction.

## Pitfall: the documented mechanism may be wrong

A skill's SKILL.md may describe automation as one layer when the live dispatch is another (this bit us: `dotfile-backup` said "Hermes cron job `dotfile-backup`" but `jobs.json` had NO such entry — the real runner was the user systemd timer `dotfiles-backup.timer`). Always cross-check the documented mechanism against the live one, and report the mismatch even when it functionally works. Offer to fix the doc, don't silently leave the discrepancy.

## Pitfall: Hermes state lives in several colliding paths

- `~/.hermes/memories/` (MEMORY.md, USER.md — active)
- `~/.hermes/memory/` (legacy notes)
- `~/.hermes/brain/` (session-brain wiki + graphify artifacts)

When a sync/backup claims it covers "memory/brain", confirm the right paths are targeted and each exists.

## Checklist

```bash
# 1. which layers reference the automation?
grep -o '"name":"[^"]*"' ~/.hermes/cron/jobs.json | grep -i <name>   # hermes cron?
systemctl --user list-unit-files | grep -i <name>                    # user systemd unit?
cat ~/.config/systemd/user/<name>.service                            # what ExecStart runs?
systemctl --user is-enabled <name>.timer && systemctl --user is-active <name>.timer
systemctl --user list-timers <name>.timer                            # LAST/PASSED/NEXT = real proof
# 2. Did it actually run / dispatch the current script?
git -C <repo> log --oneline -3                                       # daily-firing shows timestamped commits
grep -c <marker_fn> <live_script>                                    # deployed copy has new code
bash <live_script> 2>&1; echo "exit: $?"                             # clean run now
```