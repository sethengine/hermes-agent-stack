#!/usr/bin/env python3
"""
Auto-update a game's DLSS DLLs (nvngx_dlss.dll / dlssg / dlssd) to the latest
available version from the GE-Proton upscaler manifest.

Usage:
    python3 d2r-dlss-update.py /path/to/game/directory

The script fetches the manifest, finds the latest non-dev DLSS SR/FG/Depth DLLs,
compares with what's installed (by file size), and replaces if newer.
Old DLLs are backed up to /tmp/d2r-dlss-backups/.
"""

import hashlib
import json
import lzma
import os
import shutil
import sys
import urllib.request
from pathlib import Path

MANIFEST_URL = "https://loathingkernel.github.io/proton-upscalers/manifest.json"
BACKUP_DIR = Path("/tmp/d2r-dlss-backups")
USER_AGENT = "Mozilla/5.0 d2r-dlss-update/1.0"

# DLL target -> manifest key mapping
TARGETS = {
    "nvngx_dlss.dll":  "dlss",    # Super Resolution
    "nvngx_dlssg.dll": "dlss_g",  # Frame Generation
    "nvngx_dlssd.dll": "dlss_d",  # Depth / Denoiser
}


def log(msg):
    print(f"  {msg}")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as f:
        return json.loads(f.read())


def get_latest(manifest, manifest_key):
    """Get the latest non-dev entry for a given manifest key."""
    entries = [e for e in manifest[manifest_key] if not e.get("is_dev_file")]
    entries.sort(key=lambda x: x.get("version_number", 0), reverse=True)
    return entries[0] if entries else None


def download_and_decompress(url, expected_md5=None):
    """Download a file, decompress if .xz, return (data, md5)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as f:
        data = f.read()

    md5 = hashlib.md5(data).hexdigest().lower()

    if url.endswith(".xz"):
        data = lzma.decompress(data)
        md5 = hashlib.md5(data).hexdigest().lower()

    if expected_md5 and md5 != expected_md5.lower():
        raise RuntimeError(f"MD5 mismatch: got {md5}, expected {expected_md5}")

    return data, md5


def main():
    if len(sys.argv) < 2:
        print("Usage: d2r-dlss-update.py /path/to/game/directory")
        sys.exit(1)

    game_dir = Path(sys.argv[1]).resolve()
    if not game_dir.is_dir():
        print(f"ERROR: directory not found: {game_dir}")
        sys.exit(1)

    print(f"DLSS Auto-Updater")
    print(f"  Game dir: {game_dir}")
    print()

    # Fetch manifest
    log("Fetching upscaler manifest...")
    manifest = fetch_json(MANIFEST_URL)

    updated_any = False
    current_versions = {}

    for dll_name, manifest_key in TARGETS.items():
        latest = get_latest(manifest, manifest_key)
        if not latest:
            log(f"  WARNING: No entries for '{manifest_key}', skipping")
            continue

        version = latest["version"]
        internal = latest.get("internal_name", "?")
        url = latest["download_url"]
        expected_md5 = latest.get("md5_hash")

        dll_path = game_dir / dll_name
        current_size = dll_path.stat().st_size if dll_path.exists() else 0
        new_size = latest.get("file_size", 0)

        log(f"{dll_name}:")
        log(f"  Latest: {version} ({internal})")

        # Check if already up-to-date by size comparison
        if new_size and current_size == new_size and dll_path.exists():
            log(f"  Already latest ({current_size} bytes)")
            current_versions[dll_name] = version
            continue

        # Backup old
        if dll_path.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            bak = BACKUP_DIR / f"{dll_name}.{hashlib.md5(dll_path.read_bytes()).hexdigest()[:8]}"
            if not bak.exists():
                shutil.copy2(dll_path, bak)
                log(f"  Backed up to {bak.name}")

        # Download
        log(f"  Downloading {version} ({new_size // 1024}KB)...")
        try:
            data, md5 = download_and_decompress(url, expected_md5)
        except Exception as e:
            log(f"  FAILED: {e}")
            continue

        dll_path.write_bytes(data)
        log(f"  Installed: {len(data)} bytes, MD5: {md5}")
        updated_any = True
        current_versions[dll_name] = version

    print()
    if updated_any:
        print("✅ Updated to:")
    else:
        print("✅ All DLLs already at latest version")

    for dll_name, ver in current_versions.items():
        p = game_dir / dll_name
        print(f"   {dll_name} -> {ver} ({p.stat().st_size // 1024}KB)")

    print()


if __name__ == "__main__":
    main()
