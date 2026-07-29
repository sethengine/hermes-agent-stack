#!/usr/bin/env python3
"""
Generic DLSS DLL auto-updater for Steam games.

Fetches the latest nvngx_dlss.dll / dlssg / dlssd from the Proton upscaler manifest
and replaces them in the game directory. Same source GE-Proton uses internally.

Usage:
  python dlss-update.py /path/to/game/directory
  DLSS_DIR=/path/to/game python dlss-update.py

The script:
  1. Fetches https://loathingkernel.github.io/proton-upscalers/manifest.json
  2. Finds the latest non-dev DLSS SR/FG/Depth DLLs
  3. Downloads, decompresses (.xz), MD5-verifies
  4. Backs up old DLLs to /tmp/<game-basename>-dlss-backups/
  5. Replaces them in the game directory
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
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 dlss-update/1.0"

TARGETS = {
    "nvngx_dlss.dll":  "dlss",   # Super Resolution
    "nvngx_dlssg.dll": "dlss_g", # Frame Generation
    "nvngx_dlssd.dll": "dlss_d", # Depth
}

def resolve_game_dir():
    if len(sys.argv) > 1 and sys.argv[1] not in ("-h", "--help"):
        return Path(sys.argv[1])
    if "DLSS_DIR" in os.environ:
        return Path(os.environ["DLSS_DIR"])
    print(f"Usage: {sys.argv[0]} /path/to/game/directory", file=sys.stderr)
    print("  Or export DLSS_DIR=/path/to/game", file=sys.stderr)
    sys.exit(1)

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as f:
        return json.loads(f.read())

def get_latest(manifest, key):
    entries = [e for e in manifest[key] if not e.get("is_dev_file")]
    entries.sort(key=lambda x: x.get("version_number", 0), reverse=True)
    return entries[0] if entries else None

def download_and_decompress(url, expected_md5=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as f:
        data = f.read()
    if url.endswith(".xz"):
        data = lzma.decompress(data)
    md5 = hashlib.md5(data).hexdigest().lower()
    if expected_md5 and md5 != expected_md5.lower():
        raise RuntimeError(f"MD5 mismatch: got {md5}, expected {expected_md5}")
    return data, md5

def main():
    game_dir = resolve_game_dir()
    if not (game_dir / "D2R.exe").exists():
        print(f"Warning: no D2R.exe found in {game_dir} - continuing anyway")

    backup_dir = Path("/tmp") / f"{game_dir.name}-dlss-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest = fetch_json(MANIFEST_URL)
    updated = False
    current = {}

    for dll_name, manifest_key in TARGETS.items():
        latest = get_latest(manifest, manifest_key)
        if not latest:
            print(f"  No entries for {manifest_key}, skipping")
            continue

        dll_path = game_dir / dll_name
        version = latest["version"]
        size = latest.get("file_size", 0)

        if dll_path.exists() and size and dll_path.stat().st_size == size:
            current[dll_name] = version
            continue

        bak = backup_dir / f"{dll_name}.{hashlib.md5(dll_path.read_bytes()).hexdigest()[:8]}" if dll_path.exists() else None
        if bak and not bak.exists():
            shutil.copy2(dll_path, bak)

        data, _ = download_and_decompress(latest["download_url"], latest.get("md5_hash"))
        dll_path.write_bytes(data)
        updated = True
        current[dll_name] = version
        print(f"  {dll_name} -> {version} ({len(data)//1024}KB)")

    if updated:
        print(f"Updated. Backups in {backup_dir}")
    else:
        print("All already latest")

if __name__ == "__main__":
    main()
