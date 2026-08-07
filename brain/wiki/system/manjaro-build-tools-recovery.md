---
category: system
source_session: 20260726_020103_8ad5f6
date: 2026-07-29
tags: [manjaro, arch, build-tools, recovery, pacman]
---

# Manjaro Build Tools Recovery After Orphan Cleanup

Running `pacman -Qtdq | sudo pacman -Rns -` indiscriminately can remove essential build tools that happen to be orphaned.

## Tools Lost & Restored

| Tool | Purpose |
|------|---------|
| **cmake** | C++/AUR package build system |
| **meson** + **ninja** | Build system for many projects |
| **rust** (rustc/cargo) | Rust compiler |
| **go** | Go compiler |
| **cppdap** | Debug Adapter Protocol (Emacs C++ debugging) |
| **doxygen** | C++ API documentation generator |
| **typescript** | TypeScript-to-JS compiler |
| **nvm** | Node Version Manager |

**Default compiler** (GCC 16.1.1) was unaffected — only the older `gcc14` was removed.

## Recovery Command

```bash
sudo pacman -S cmake meson ninja rust go cppdap doxygen typescript nvm
```

## Prevention: Pin Essential Tools

```bash
sudo pacman -D --asexplicit cmake meson ninja rust go cppdap doxygen typescript nvm
```

This marks them as explicitly installed so `pacman -Qtdq` never lists them again.

## Related

- [[manjaro-root-disk-cleanup]]
- `man pacman` · Section on package origin and explicit vs. dependency installs
