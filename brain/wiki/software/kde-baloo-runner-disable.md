---
source: 20260703_231509_6397bb
category: software
date: 2026-07-03
tags: [kde, baloo, krunner, file-indexer, systemd, user-service]
---

# Properly Disabling KDE Baloo File Indexer Runner

Running `balooctl6 disable` only prevents the Baloo file indexer daemon from starting. The KDE user service `plasma-baloorunner.service` (the KRunner provider for Baloo) continues to run because `balooctl` doesn't affect it.

**Symptoms:** Baloo is reported as disabled by `balooctl6 status`, but `ps aux | grep baloo` or `systemctl --user status plasma-baloorunner.service` shows it's still active.

**Fix — stop, disable, and mask:**
```
systemctl --user stop plasma-baloorunner.service
systemctl --user disable plasma-baloorunner.service
systemctl --user mask plasma-baloorunner.service
```

**Clean up the database:**
```
rm -rf ~/.local/share/baloo
```

**KRunner compatibility:** KRunner works fully without Baloo. Only file **content** search (searching inside files) is lost. App launching, calculator, system commands, web shortcuts, window switching all work fine.

The service is `static` type — it ships as part of `plasma-workspace.target` and gets restarted every login. Masking is required to permanently prevent it.
