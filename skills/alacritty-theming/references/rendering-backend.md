# Alacritty Rendering Backend

How to control Alacritty's OpenGL / GLES rendering backend — config options, platform details, and source-level behavior.

## Config options (`[debug]` section)

```toml
[debug]
renderer = "Gles2"       # Force GLES 2.0 with extensions (dual-source blending)
prefer_egl = true         # Force EGL display API instead of GLX on X11
```

### `renderer` values

| Value | Behavior |
|---|---|
| `"Glsl3"` | Desktop OpenGL 3.3 Core (default when available) |
| `"Gles2"` | GLES 2.0 with optional extensions like dual-source blending |
| `"Gles2Pure"` | Strict GLES 2.0 — no extensions, maximum compatibility |

### `prefer_egl`

- On Linux X11: default is `GlxThenEgl`. Setting `prefer_egl = true` flips to `EglThenGlx`.
- On Wayland: EGL is already the only option — this setting is redundant.
- On Windows: flips `WglThenEgl` to `EglThenWgl`.
- On macOS: ignored (CGL only).

No environment variable exists for any of this — it's purely config-driven.

## Context creation priority chain

From [`platform.rs`](https://github.com/alacritty/alacritty/blob/master/alacritty/src/renderer/platform.rs#L108-L118):

1. **OpenGL 3.3 Core** — tried first
2. **GLES 2.0** — tried second (comment: *"Try gles before OpenGL 2.1 as it tends to be more stable"*)
3. **OpenGL 2.1 Compatibility** — last resort

When `renderer` is explicitly set in config, Alacritty skips the auto-detection and forces that specific renderer regardless of what the context creation returns.

## Source layout

| File | Role |
|---|---|
| `alacritty/src/renderer/platform.rs` | Display API selection, GL config picking, context creation priority |
| `alacritty/src/renderer/mod.rs` | `TextRendererProvider` enum (`Gles2` \| `Glsl3`), renderer dispatch |
| `alacritty/src/renderer/text/mod.rs` | `Gles2Renderer` and `Glsl3Renderer` structs, shared text rendering trait |
| `alacritty/src/config/debug.rs` | `RendererPreference` enum, `Debug` struct with `renderer` and `prefer_egl` fields |

## Key source snippets

### RendererPreference enum (`debug.rs` line 51-56):
```rust
pub enum RendererPreference {
    /// OpenGL 3.3 renderer.
    Glsl3,
    /// GLES 2 renderer, with optional extensions like dual source blending.
    Gles2,
    /// Pure GLES 2 renderer.
    Gles2Pure,
}
```

### Context creation order (`platform.rs` line 108-112):
```rust
let apis = [
    (ContextApi::OpenGl(Some(Version::new(3, 3))), GlProfile::Core),
    // Try gles before OpenGL 2.1 as it tends to be more stable.
    (ContextApi::Gles(Some(Version::new(2, 0))), GlProfile::Core),
    (ContextApi::OpenGl(Some(Version::new(2, 1))), GlProfile::Compatibility),
];
```

### EGL preference on X11 (`platform.rs` line 43-48):
```rust
let preference = if _prefer_egl {
    DisplayApiPreference::EglThenGlx(Box::new(x11::register_xlib_error_hook))
} else {
    DisplayApiPreference::GlxThenEgl(Box::new(x11::register_xlib_error_hook))
};
```

## When to use GLES

- **NVIDIA + XWayland**: GLES2 + EGL avoids GLX translation overhead and can be noticeably faster
- **Debugging GPU context issues**: GLES2 is more portable and often more stable than OpenGL 3.3
- **Embedded/ARM systems**: Only GLES may be available
- **User preference**: GLES2 was reported as "faster and more reliable" on RTX 5060 Ti / KDE Wayland

## Verification

Check what's actually in use:
```bash
# See current config
alacritty msg get-config | grep -A3 debug

# Check GL info at startup (run alacritty with logging)
alacritty -vvv 2>&1 | grep -i "gl\|gles\|egl\|renderer"
```
