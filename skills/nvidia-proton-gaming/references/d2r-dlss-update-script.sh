#!/usr/bin/env bash
# D2R DLSS Auto-Updater
# Downloads latest DLSS DLLs from the loathingkernel manifest and replaces
# them in the D2R game directory. Same source GE-Proton uses internally.
# Run manually or set as a cron job.
# Source: /home/sethengine/.local/bin/d2r-dlss-update (Python script)
#
# The Python version is more robust. Place it at ~/.local/bin/d2r-dlss-update
# and set as Steam launch option:
#   /home/sethengine/.local/bin/d2r-dlss-update && mangohud %command%
# Or as a cron job (no_agent=true):
#   script: d2r-dlss-update
#   schedule: 0 10 * * 1 (weekly Monday 10AM)
echo "See Python script at ~/.local/bin/d2r-dlss-update"
