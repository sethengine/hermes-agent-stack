# KWIN_COMPOSE — valid values for KWin 6 (source-verified, 2026-07)

Session: user asked "all valid KWIN_COMPOSE values for KWin on this system".
Verified from **KWin v6.7.3 source** (matches installed `kwin 6.7.3-1.1` on Manjaro),
cross-checked against the installed binary and the live environment.

## Bottom line

On KWin 6.x (Plasma 6) only **three values do anything**:

| Value | Effect | Status |
|-------|--------|--------|
| `O2` | Force **OpenGL 2** compositing. Skips the driver's `recommendedCompositor()` check (normally causes fallback). | ✅ Valid |
| `O2ES` | Force **OpenGL 2 + EGL platform** (OpenGL ES interface). Same as O2 plus forces EGL. | ✅ Valid |
| `Q` | Force **QPainter** (software) compositing. | ✅ Valid |
| `O` | Selects OpenGL in options → but compositor-level check hard-fails → **KWin exits**. | ⚠️ Trap from old docs |
| `X`, `N`, anything else | Logs `"Unknown KWIN_COMPOSE mode set, ignoring"` → falls back to kwinrc (default OpenGL) → OpenGL attempt fails → **KWin exits**. | ❌ Invalid on 6.x |

## Why `O`/`X`/`N` are dead on KWin 6

`KWIN_COMPOSE` is parsed in exactly **two** places in 6.7.3 (GitHub code search confirms
no other references anywhere in the repo):

1. **`src/options.cpp`** — `switch (c[0])` on the first char. Only `case 'O'` (OpenGL) and
   `case 'Q'` (QPainter); `default` → `"Unknown KWIN_COMPOSE mode set, ignoring"`.
   The old `'N'` (NoCompositing) and `'X'` (XRender) cases are gone.
2. **`src/compositor.cpp`** (`attemptOpenGLCompositing`) — exact-match on the FULL string:
   `qstrcmp(forceEnv, "O2") == 0 || qstrcmp(forceEnv, "O2ES") == 0` → enforce OpenGL.
   **Any other non-empty value returns false** (OpenGL attempt fails), and when the first
   candidate compositor fails while `KWIN_COMPOSE` is set, KWin logs
   `"Could not fulfill the requested compositing mode in KWIN_COMPOSE"` and **quits**
   instead of falling back.

So `KWIN_COMPOSE=O` (a KDE4-era value still quoted by old tutorials) makes KWin exit at
login. Symptom: session dies right after SDDM, journal shows the "Could not fulfill" line.

XRender itself was deleted in the Plasma 6 port; the DRM (Wayland) backend's
`supportedCompositors()` returns only `{OpenGL, QPainter}` in 6.7.3 (master shows `{OpenGL}`
only — QPainter dropped from DRM post-6.7). Wayland has no `NoCompositing` either.

## Historical values (for reading old docs / other machines)

| Version | Parsed values (verified in source) |
|---------|------------------------------------|
| KWin 4.x (kde-workspace) | `O` OpenGL, `X` XRender, `Q` QPainter, `N` none |
| KWin 5.27.x | `O`, `Q`, `N`; `O2ES` additionally forces EGL; `O2`/`O2ES` enforce OpenGL at compositor level; `X` already removed |
| KWin 6.x | `O2`, `O2ES`, `Q` — only |

The `OF`/`XF` "FBO variant" values occasionally quoted from the old community wiki
(`community.kde.org/KWin/Environment_Variables`, now antibot-blocked) could NOT be
confirmed in any source — treat as unverified legacy folklore.

## This user's machine

Live env (`env | grep -i KWIN`) already contains:

```
KWIN_COMPOSE=O2ES
KWIN_FORCE_SW_CURSOR=0
KWIN_TRIPLE_BUFFER=0
KWIN_DRM_BACKEND=drm
KWIN_DRM_USE_EGL_STREAMS=0
KWIN_DRM_ALLOW_TEARING=1
KWIN_DRM_DISABLE_TRIPLE_BUFFERING=1
KWIN_DRM_OVERRIDE_SAFETY_MARGIN=300
```

`KWIN_COMPOSE=O2ES` is the correct modern value for NVIDIA + Wayland (forces EGL, skips
driver recommendation). Leave it. If a login ever fails with "Could not fulfill the
requested compositing mode in KWIN_COMPOSE", look for a stale `KWIN_COMPOSE=O` set by an
old KDE4-era guide.

## LLM-guide hallucinations: `O2V`, "latest OpenGL 4" flags

Follow-up session: user reported "some LLM guides said KWIN_COMPOSE=O2V is a good option or
latest OpenGL 4 — what is the flag?"

Verified: **`O2V` does not exist anywhere in KWin 6 source.** GitHub code search finds only
two `KWIN_COMPOSE` references in the repo (options.cpp + compositor.cpp), and neither
recognizes `O2V`:

- `options.cpp` dispatches on `c[0]` only — `O2V` starts with `O` → maps to OpenGL mode.
- `compositor.cpp` does an **exact full-string match** against `"O2"`/`"O2ES"` — `O2V`
  matches neither → `attemptOpenGLCompositing()` returns false → compositor fails → KWin
  exits with "Could not fulfill". Same fate as plain `O`.

**There is no "OpenGL version" flag at all.** `KWIN_COMPOSE` selects a compositing
*backend* (OpenGL vs QPainter vs none), never a GL version. The actual GL version
negotiation is the NVIDIA driver's job: KWin only checks a GL 2.0 minimum
(`hasGLVersion(2, 0)` in `GLPlatform`), and the driver's `recommendedCompositor()` answer
determines which compositor is attempted. `OF`/`XF`/`O2V`/`N`/anything not exactly
`O2`/`O2ES`/`Q` are all equally invalid on 6.x.

## Can you switch KWIN_COMPOSE without relog? (No — verified)

Follow-up: user asked how to apply a new compositor flag without logging out.

Verified from v6.7.3 source — **there is no clean live-switch path; a relog (or at least
a session restart) is required.** The mechanics:

1. **Read once at compositor start.** `attemptOpenGLCompositing()` calls
   `qgetenv("KWIN_COMPOSE")` at startup. Not wired to KConfig's `configChanged()`, not
   re-read on reconfiguration.
2. **D-Bus reinitialize exists but is useless.** `CompositorDBusInterface::reinitialize()`
   (qdbus `org.kde.KWin /Compositor reinitialize`) → `Compositor::reinitialize()` →
   `stop(); start()` → **re-runs `qgetenv("KWIN_COMPOSE")`**. BUT it re-reads the running
   process's own environment, and a process's env cannot be mutated from outside
   (`/proc/<pid>/environ` is read-only to other processes). The re-read returns the same
   old value → zero effect.
3. **`kwin_wayland --replace` is a trap on Wayland.** `main_wayland.cpp`: `--replace`
   sends D-Bus `org.kde.KWin.replace` to the running instance (which exits with code 133)
   then **exits itself** (`return 0`). The actual restart is done by systemd
   (`kwin_wayland_wrapper` / `plasma-kwin_wayland.service`), which inherits the **systemd
   user environment, not your shell's**. `export KWIN_COMPOSE=O2; kwin_wayland --replace`
   therefore restarts with the OLD value. To make it stick you must first
   `systemctl --user set-environment KWIN_COMPOSE=O2`, and even then the compositor
   restart on Wayland kills plasmashell + every Wayland client → effectively a session
   restart.

The only technically-possible live path is ptrace/gdb `setenv()` into the kwin process +
D-Bus reinitialize — do not recommend; it can crash the session.

**Correct procedure to change KWIN_COMPOSE:** set it in the session environment
(`~/.config/plasma-workspace/env/`, `~/.config/environment.d/`, or
`systemctl --user set-environment`), then log out/in.



1. Pin the exact installed version: `pacman -Q kwin` → fetch source at that exact tag:
   `https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/options.cpp` (raw host bypasses
   GitHub's antibot; the github.com HTML pages 404/blocks).
2. When `web_extract` BM25-filters or truncates the middle of a big file, the full text is
   cached at `~/.hermes/cache/web/*.md` — grep it for the symbol:
   `grep -o 'getenv("KWIN_COMPOSE")[^}]*}' <cached-file>`.
3. Cross-verify against the installed binary: `strings -a /usr/bin/kwin_wayland | grep KWIN_COMPOSE`
   (log strings are UTF-16 and won't show; the env-var name is ASCII so it does).
4. Check the live environment: `env | grep -i KWIN`.
5. Trace history via older tags (`v5.27.12`, kde-workspace `master` for KDE4) to explain
   which values older docs mention and when they were dropped.

For the verified 6.7.3 picture of what GL version KWin actually requests vs. what NVIDIA
delivers (requests 3.1, gets 4.6 — no way to pick 3 vs 4), see "GL version negotiation"
below.

## GL version negotiation: KWin requests 3.1, NVIDIA delivers 4.6 (no 3-vs-4 choice)

Follow-up: user asked "how to force OpenGL 3 or 4 for KWin on NVIDIA".

Verified from v6.7.3 `src/opengl/eglcontext.cpp`:

- **Desktop GL candidates all call `setVersion(3, 1)`** — grep shows 5× `setVersion(3, 1)`
  and 0× any higher version, applied via EGL_KHR_create_context attributes
  (`EGL_CONTEXT_MAJOR_VERSION/MINOR_VERSION`). GLES candidates call `setVersion(2)` (ES 2.0).
- **The delivered version is the driver's choice.** The requested version is a minimum;
  NVIDIA returns its maximum. Verified live on this machine (driver 610.43.03):
  `eglinfo -B` → `OpenGL core profile version: 4.6.0 NVIDIA 610.43.03` (GLES max is 3.2).
- **KWin adapts to what it got via `hasVersion()` feature checks:** 3.0 (extension query),
  3.2 (indexed quads), 3.3 (texture swizzle — `checkTextureSwizzleSupport`), 4.2 (texture
  storage — `checkTextureStorageSupport`), 4.4 (buffer storage — `m_haveBufferStorage`).
- **No config selects 3 vs 4.** Only the O2 vs O2ES backend choice exists. Forcing a
  literal 3.3/4.0 context would require patching `setVersion()` and rebuilding KWin.

## Plasma 6.8: desktop OpenGL dropped — KWin is GLES-only

Announced 2026-07 (Phoronix 2026-07-04, KWin merge request !9488 by Xaver Hugl, echoed by
fosslinux 2026-07-10): KWin drops the desktop GL path and runs **OpenGL ES only** — "the
various incompatibilities between desktop GL and OpenGL ES cause problems again and
again." Implications:

- `KWIN_COMPOSE=O2` stops being meaningful after the 6.8 upgrade; KWin is GLES regardless.
- This is compositor-only; desktop OpenGL outside KWin (games, apps) is unaffected.
- On this user's box there is no functional reason to prefer O2 over O2ES — delivered GL
  is 4.6, delivered ES is 3.2, and both satisfy every feature KWin needs.

## env-dir landmine: `~/.config/plasma-workspace/env/*.sh` last-wins

While proving the "`KWIN_COMPOSE=O` kills the next login" claim, found a real conflict on
this machine:

- `kwin-opengl.sh` → `export KWIN_COMPOSE=O2ES`
- `kwin.sh` (line 6, sorts later) → `export KWIN_COMPOSE=O` ← **was live**, would override
  to an invalid value at next login and kill the session.

Mechanics: Plasma sources `~/.config/plasma-workspace/env/*.sh` at login in lexicographic
order; **last export wins**. The `kwin.sh` line has since been commented out (file went
185 → 186 bytes, mtime after the warning), but the diagnostic pattern is durable:

```bash
grep -l 'export KWIN_COMPOSE' ~/.config/plasma-workspace/env/*.sh | sort   # who sets it
unset KWIN_COMPOSE; for f in $(ls ~/.config/plasma-workspace/env/*.sh | sort); do . "$f" 2>/dev/null; done; echo "final: $KWIN_COMPOSE"
systemctl --user show-environment | grep -i kwin   # systemd user env can carry stale values too
```

`kwin-opengl.sh` is the user's designated KWin backend switch file (name is arbitrary —
only content + directory matter).

## Online corroboration (KDE bugs + press)

- KDE Bug 484199 (kwin fails to start with bad KWIN_COMPOSE): shows the real-world fatal
  `kwin_core: Could not fulfill the requested compositing mode in KWIN_COMPOSE: 1 . Exiting.`
  and the result — session runs with NO window manager (on Wayland: session dies).
- KDE Bug 456372 comment: "KWIN_COMPOSE=O2ES means you're forcing KWin into OpenGLES
  rendering" — corroborates O2ES semantics.
- fosslinux 2026-07-10: "Setting KWIN_COMPOSE=O2ES forces OpenGL ES. Setting
  KWIN_COMPOSE=O2 forces Desktop OpenGL. After changing this, you need to log out and
  back in" (also the source of the Plasma 6.8 GLES-only news).
- KWin wiki (invent.kde.org/plasma/kwin/-/wikis/Environment-Variables): "KWIN_COMPOSE
  enforces a compositing backend" (page is JS-rendered — use the diff view or search
  snippet to read it).
- Phoronix 2026-07-04 "KWin Compositor In KDE Plasma 6.8 Drops Support For Desktop
  OpenGL".

## Live verification commands (add to recipe)

- Backend in use: `qdbus6 org.kde.KWin /Compositor compositingType` → `gl2` (desktop GL)
  or `gles`.
- Driver GL/GLES maxima: `eglinfo -B | grep -iE 'OpenGL core profile version|OpenGL ES profile version'`
  (glxinfo shows the same but via GLX, which KWin 6 doesn't use).
- KWin's own GL init lines are qCDebug-level and usually absent from `journalctl --user -b
  -u plasma-kwin_wayland.service` — don't expect them; the D-Bus/eglinfo checks above are
  the reliable probes.
- Grepping minified source cached by web_extract: underscores are escaped as `\_`, so
  plain `grep setVersion` misses — use the escaped form or `grep -o 'setVersion([0-9, ]*)'`
  on the cache file.

## Sources

- https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/options.cpp
- https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/compositor.cpp
- https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/dbusinterface.cpp
- https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/main_wayland.cpp
- https://raw.githubusercontent.com/KDE/kwin/v6.7.3/src/backends/drm/drm_backend.cpp
- https://raw.githubusercontent.com/KDE/kwin/v5.27.12/src/options.cpp
- https://raw.githubusercontent.com/KDE/kwin/v5.27.12/src/composite.cpp
- https://raw.githubusercontent.com/KDE/kde-workspace/master/kwin/options.cpp
- GitHub code search: `KWIN_COMPOSE repo:KDE/kwin`
