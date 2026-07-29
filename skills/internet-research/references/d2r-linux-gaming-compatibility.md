# Diablo 2 Resurrected — Linux Gaming Compatibility Research

**Source:** ProtonDB reports for Steam App ID 2536520 (Infernal Edition)
**Data collected:** July 2026 — 39 reports, Platinum rating, Steam Deck Verified

## Known Issues (NVIDIA + Wayland + Linux)

### 1. Fullscreen / Resolution Settings Don't Stick
- **Symptoms:** Game launches in fixed window, resolution options missing, or 1/4-screen render bug (only top-left quadrant visible)
- **Workarounds:**
  - `Alt+Enter` to toggle windowed→fullscreen (fixes 1/4-screen bug on Proton 10.0-3 + NVIDIA 590)
  - Switch to **Proton Experimental** if Proton 10 has fullscreen issues (RTX 4070 Ti, EndeavourOS confirmed)
  - Switch to **GE-Proton10-34** — specifically reported to fix "limited to fixed window, no resolution change" on RTX 4070 + CachyOS + NVIDIA 595.58.03

### 2. Random Crashes in Fullscreen
- **Pattern:** Game runs fine in windowed mode but crashes in fullscreen
- **Reported on:** Pop!_OS + RTX 3060 Ti (Proton Experimental, driver 535)
- **Unrelated to distro swaps:** One user (RTX 3070 Ti, NVIDIA 590) tried 3 distros and 3 GPU drivers — still crashes 5-60 min into play

### 3. Gamepad Cursor Flicker
- Circular inventory cursor fades/flickers when using analog stick on controller
- Not fixed across Proton versions (Proton 10, Experimental, proton-cachyos all affected)

### 4. Battle.net Login / ClientSDK Issue
- Fresh install shows: *"You have not been online in the last 30 days"*
- **Fix:**
  ```
  mkdir -p "/path/to/pfx/drive_c/users/steamuser/AppData/Local/Blizzard Entertainment/ClientSdk"
  ```
  Where the compatdata path is: `~/.local/share/Steam/steamapps/compatdata/2536520/pfx/drive_c/...`

## Working Configurations (NVIDIA)

| Distro | GPU | Proton | Driver | Notes |
|--------|-----|--------|--------|-------|
| Fedora 43 | RTX 5070 Ti | 10.0-3 | 590.44.01 | OOTB flawless |
| Fedora 43 | RTX 5070 Ti | 10.0-3 | 580.119.02 | OOTB flawless |
| Bazzite | RTX 5070 Ti | 10.0-3 | 590.44.01 | No tinkering |
| CachyOS | RTX 3070 | 10.0-3 | 590.48.01 | DLSS, fullscreen, all graphics work |
| CachyOS | RTX 3070 | CachyOS SLR | 595.45.04 | Works, ~3 crashes in 30h |

## Launch Options Collected from Reports

```bash
# Server selection (Steam version lacks Battle.net launcher)
-address eu.actual.battle.net    # Europe
-address us.actual.battle.net    # Americas
-address kr.actual.battle.net    # Asia

# Performance
game-performance %command%
gamemoderun %command%

# Wayland on ProtonGE
PROTON_ENABLE_WAYLAND=1 WAYLANDDRV_PRIMARY_MONITOR=DP-1 %command%

# Disable Steam Deck controller mode (for Bazzite and similar Deck-likes)
SteamDeck=0 %command% -address us.actual.battle.net

# Disable Wayland (known to workaround some issues)
PROTON_ENABLE_WAYLAND=0 %command%
```

## Key Takeaways

- **Platinum rating may be optimistic** — several users report frequent crashes that are unacceptable for the rating
- **Proton 10 is problematic for fullscreen** on NVIDIA — try Experimental or GE-Proton10-34 first
- **Turning off Vsync** helps with FPS drops/stability per user reports
- **Save file path** for manual character transfer from Battle.net version: `~/.local/share/Steam/steamapps/compatdata/2536520/pfx/drive_c/users/steamuser/Saved Games/Diablo II Resurrected/`

## Research Methodology

This data was extracted from ProtonDB (JS-heavy React SPA) using Playwright browser automation:
1. Navigate to `https://www.protondb.com/app/2536520`
2. Wait 5s for React hydration and API fetch
3. Capture full accessibility tree with `browser_snapshot()`
4. Parse structured report elements from the YAML output
