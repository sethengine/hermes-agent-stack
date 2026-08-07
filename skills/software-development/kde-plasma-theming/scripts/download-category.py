#!/usr/bin/env python3
"""
Download a single KDE Store category.

Per-category downloader for reliable chunked execution. Each category
completes in 30-60 minutes (well under session timeouts), making this
more reliable than monolithic multi-category scripts.

Usage:
  python3 download-category.py 722 01-global-themes-p6
  python3 download-category.py 717 02-window-decorations-p6
  python3 download-category.py 112 03-color-schemes
  python3 download-category.py 104 04-plasma-styles
  python3 download-category.py 114 05-aurorae-decorations
"""

import sys, json, time, re, subprocess
from pathlib import Path

API = "https://api.kde-look.org/ocs/v1/content/data"
GAP = 10  # seconds between JWT resolves (proven safe against rate limits)
PAGE_SIZE = 100
MIN_BYTES = 500  # rate-limit XML error is ~147 bytes; real themes are larger
UA = "Mozilla/5.0 (X11; Linux x86_64) KDE Plasma 6"

cat_id = int(sys.argv[1])
folder = sys.argv[2]
dest = Path.home() / "kde6-themes-archive" / folder
dest.mkdir(parents=True, exist_ok=True)

def log(m):
    print(m, flush=True)

# Clean up error XML files from aborted runs
for f in dest.iterdir():
    if f.is_file() and f.stat().st_size < MIN_BYTES:
        f.unlink()

log(f"\n{'='*60}")
log(f"Downloading category {cat_id} -> {folder}")
log(f"{'='*60}")

page = 1
cdl = cex = cerr = crl = 0
cmb = 0.0
total = 0
start = time.time()

while True:
    r = subprocess.run(["curl", "-s",
        f"{API}?categories={cat_id}&format=json&page={page}&pagesize={PAGE_SIZE}",
        "-H", f"User-Agent: {UA}"], capture_output=True, text=True, timeout=30)
    if not r.stdout:
        log(f"  API error at page {page}, stopping"); break
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', r.stdout)
    data = json.loads(cleaned)
    if data.get("status") != "ok":
        log(f"  API status error at page {page}, stopping"); break

    if total == 0:
        total = data.get("totalitems", 0)
        log(f"  Total: {total}")

    items = data.get("data", [])
    if not items: break
    log(f"  Page {page}: {len(items)} items")

    for i, item in enumerate(items):
        name = item.get("name", "?")
        jwt = item.get("downloadlink1", "")
        fname = item.get("downloadname1", "")
        exp_kb = int(item.get("downloadsize1", 0))
        n = (page - 1) * PAGE_SIZE + i + 1

        if not jwt or not fname:
            cerr += 1
            log(f"  {n:4d}/{total} NO-LINK {name[:30]}")
            time.sleep(GAP); continue

        safe = re.sub(r"[^a-zA-Z0-9._()-]", "_", fname.replace(" ", "_"))
        dpath = dest / safe

        if dpath.exists() and dpath.stat().st_size >= MIN_BYTES:
            if exp_kb <= 0 or 0.5 < (dpath.stat().st_size/1024)/exp_kb < 3.0:
                cex += 1
                time.sleep(GAP)
                continue

        # Resolve JWT → CDN URL (bodyless GET, avoids heavy rate-limit quota)
        r2 = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{redirect_url}",
            "--max-time", "30", "-H", f"User-Agent: {UA}",
            "-H", "Referer: https://store.kde.org/", jwt],
            capture_output=True, text=True, timeout=35)
        cdn = r2.stdout.strip()

        if len(cdn) < 100:
            crl += 1
            if crl <= 5:
                log(f"  {n:4d}/{total} RL       {name[:30]}")
            time.sleep(GAP)
            continue

        # Download from CDN (no rate limit)
        r3 = subprocess.run(["curl", "-sL", "-o", str(dpath), "--max-time", "120",
            "-H", f"User-Agent: {UA}", cdn],
            capture_output=True, text=True, timeout=130)

        if dpath.exists() and dpath.stat().st_size >= MIN_BYTES:
            cdl += 1
            cmb += dpath.stat().st_size / 1048576
            log(f"  {n:4d}/{total} OK       {name[:30]:30s} {dpath.stat().st_size/1024:.0f}KB")
        else:
            dpath.unlink(missing_ok=True)
            cerr += 1
            log(f"  {n:4d}/{total} FAIL     {name[:30]}")

        # Progress summary after every item
        elapsed_m = (time.time() - start) / 60
        total_done = cdl + cex + cerr + crl
        rate = total_done / max(elapsed_m, 0.1)
        eta_m = (total - total_done) / max(rate, 0.1)
        log(f"  + Total: D:{cdl} E:{cex} ✗:{cerr} RL:{crl} | "
            f"{cmb:.0f}MB | {rate*60:.0f}/h | ETA {eta_m:.0f}m")

        time.sleep(GAP)

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    if page >= total_pages: break
    page += 1
    time.sleep(1)

elapsed = time.time() - start
h, m, s = int(elapsed//3600), int((elapsed%3600)//60), int(elapsed%60)
log(f"\n  [{folder}] D:{cdl} E:{cex} ✗:{cerr} RL:{crl} = {cmb:.0f}MB in {h}h{m}m{s}s")

with open(dest / "manifest.json", "w") as f:
    json.dump({"cat_id": cat_id, "folder": folder, "ok": cdl, "existed": cex,
               "errors": cerr, "rate_limited": crl, "size_mb": round(cmb, 1)}, f, indent=2)
