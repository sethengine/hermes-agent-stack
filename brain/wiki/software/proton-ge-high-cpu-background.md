---
source: 20260704_002641_eff621
category: software
date: 2026-07-04
tags: [proton, ge, wine, gaming, cpu, background, steam]
---

# Proton GE High CPU Usage in Background

Proton GE (GlitchEgg) can leave hung Wine/Proton background processes consuming high CPU after game exit. These orphaned processes spin on CPU doing nothing useful.

**Diagnosis:**
```
ps aux | grep -E 'proton|wine|steam' | grep -v grep | sort -nrk 3
top -b -n 1 | grep -iE 'proton|wine|steam'
```

**Fix — kill all hung Proton/Wine processes:**
```
pkill -9 -e wineserver 2>/dev/null
pkill -9 -e "proton" 2>/dev/null
pkill -9 -e wine 2>/dev/null
pkill -9 -e "steam-runtime" 2>/dev/null
```

**Prevention:** After closing a Proton game, check `top` for leftover `wineserver` or `proton` processes. The `pkill -9` chain can be aliased for quick cleanup.

[[dead-space-remake-proton-directx-crash]]
