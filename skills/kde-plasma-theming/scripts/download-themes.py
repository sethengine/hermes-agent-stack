#!/usr/bin/env python3
"""
KDE Plasma 6 Themes Bulk Downloader (v4)

Downloads all items from KDE Store categories via the OCS API.
3-phase pipeline: collect metadata → resolve JWT→CDN → download from CDN.
Handles the aggressive rate limiting on files*.pling.com
with proven 10-second gap strategy.

Usage:
  python3 download_themes.py                    # all categories
  python3 download_themes.py --category 722     # single category
  python3 download_themes.py --delay 10 --dest ~/themes
"""

import json, time, re, subprocess, sys, argparse
from pathlib import Path

API = "https://api.kde-look.org/ocs/v1/content/data"
PAGE_SIZE = 100
UA = "Mozilla/5.0 (X11; Linux x86_64) KDE Plasma 6"
MIN_BYTES = 500  # error XML is ~147 bytes

DEFAULT_CATEGORIES = [
    (722, "01-global-themes-p6", "Global Themes (Plasma 6)"),
    (717, "02-window-decorations-p6", "Plasma 6 Window Decorations"),
    (112, "03-color-schemes", "Plasma Color Schemes"),
    (104, "04-plasma-styles", "Plasma Themes / Styles"),
    (114, "05-aurorae-decorations", "Aurorae Window Decorations"),
]


def log(m):
    print(m, flush=True)


def api_get(url):
    r = subprocess.run(["curl", "-s", url, "-H", f"User-Agent: {UA}"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode == 0 and r.stdout:
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', r.stdout)
        return json.loads(cleaned)
    return None


def resolve_jwt(jwt_url):
    """Resolve JWT→CDN URL via 302 redirect (bodyless)."""
    r = subprocess.run([
        "curl", "-s", "-o", "/dev/null", "-w", "%{redirect_url}",
        "--max-time", "30",
        "-H", f"User-Agent: {UA}",
        "-H", "Referer: https://store.kde.org/",
        jwt_url
    ], capture_output=True, text=True, timeout=35)
    cdn = r.stdout.strip()
    return cdn if len(cdn) > 100 else None


def dl_cdn(cdn_url, dpath):
    """Download from CDN (no rate limit)."""
    r = subprocess.run([
        "curl", "-sL", "-o", str(dpath), "--max-time", "120",
        "-H", f"User-Agent: {UA}", cdn_url
    ], capture_output=True, text=True, timeout=130)
    if dpath.exists() and dpath.stat().st_size >= MIN_BYTES:
        return dpath.stat().st_size / 1024
    dpath.unlink(missing_ok=True)
    return None


def process_item(item, dest, gap):
    """Full pipeline for one item: check, resolve, download."""
    name = item.get("name", "?")
    jwt = item.get("downloadlink1", "")
    fname = item.get("downloadname1", "")
    exp_kb = int(item.get("downloadsize1", 0))

    if not jwt or not fname:
        return "no_link"

    safe = re.sub(r"[^a-zA-Z0-9._()-]", "_", fname.replace(" ", "_"))
    dpath = dest / safe

    # Skip if already exists and size is reasonable
    if dpath.exists() and dpath.stat().st_size >= MIN_BYTES:
        if exp_kb <= 0 or 0.5 < (dpath.stat().st_size / 1024) / exp_kb < 3.0:
            return "exists"

    # Phase 2: Resolve JWT → CDN
    cdn = resolve_jwt(jwt)
    if not cdn:
        return "rate_limited"

    # Phase 3: Download from CDN
    result = dl_cdn(cdn, dpath)
    if result:
        return result  # size in KB
    return "dl_failed"


def main():
    parser = argparse.ArgumentParser(description="Bulk download KDE Plasma 6 themes")
    parser.add_argument("--category", type=int, help="Single category ID")
    parser.add_argument("--delay", type=int, default=10,
                        help="Seconds between JWT resolves (default: 10) — proven safe")
    parser.add_argument("--dest", default=str(Path.home() / "kde6-themes-archive"),
                        help="Output directory")
    args = parser.parse_args()

    base = Path(args.dest)
    base.mkdir(parents=True, exist_ok=True)

    categories = [c for c in DEFAULT_CATEGORIES
                  if not args.category or c[0] == args.category]

    stats = {"dl": 0, "ex": 0, "err": 0, "rl": 0, "mb": 0.0}
    start = time.time()

    # Clean tiny error files from aborted runs
    for _, folder, _ in categories:
        d = base / folder
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and f.stat().st_size < MIN_BYTES:
                    f.unlink()

    for cat_id, folder, cat_name in categories:
        dest = base / folder
        dest.mkdir(parents=True, exist_ok=True)
        log(f"\n[{folder}] {cat_name} (cat={cat_id})")

        page = 1
        total = 0
        cdl = cex = cerr = crl = 0
        cmb = 0.0

        while True:
            data = api_get(f"{API}?categories={cat_id}"
                           f"&format=json&page={page}&pagesize={PAGE_SIZE}")
            if not data or data.get("status") != "ok":
                log(f"  API error at page {page}")
                break
            if total == 0:
                total = data.get("totalitems", 0)
                log(f"  Total: {total}")
            items = data.get("data", [])
            if not items:
                break

            for i, item in enumerate(items):
                result = process_item(item, dest, args.delay)
                n = (page - 1) * PAGE_SIZE + i + 1

                if isinstance(result, float):
                    cdl += 1
                    cmb += result / 1024
                elif result == "exists":
                    cex += 1
                elif result == "rate_limited":
                    crl += 1
                elif result == "no_link":
                    cerr += 1
                else:
                    cerr += 1

                # Progress every 10 items
                if n % 10 == 0 or i == len(items) - 1:
                    pct = min(99, int(n / total * 100)) if total else 0
                    em = (time.time() - start) / 60
                    rate = n / max(em, 0.5)
                    eta_m = (total - n) / max(rate, 0.5)
                    log(f"  [{n}/{total}] {pct}% | "
                        f"D:{cdl} E:{cex} ✗:{cerr} RL:{crl} | "
                        f"{cmb:.0f}MB | {rate:.0f}/h | ETA {eta_m:.0f}m")

                time.sleep(args.delay)

            total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
            if page >= total_pages:
                break
            page += 1
            time.sleep(1)

        log(f"  [{folder}] D:{cdl} E:{cex} ✗:{cerr} RL:{crl} = {cmb:.0f}MB")
        stats["dl"] += cdl
        stats["ex"] += cex
        stats["err"] += cerr
        stats["rl"] += crl
        stats["mb"] += cmb

        with open(dest / "manifest.json", "w") as f:
            json.dump({
                "ok": cdl, "existed": cex, "errors": cerr,
                "rate_limited": crl, "size_mb": round(cmb, 1)
            }, f, indent=2)

    elapsed = time.time() - start
    h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
    log(f"\n{'=' * 60}")
    log(f"COMPLETE: D:{stats['dl']} E:{stats['ex']} ✗:{stats['err']} RL:{stats['rl']}")
    log(f"Total: {stats['mb']:.0f}MB in {h}h{m}m{s}s")
    log(f"Location: {base}")

    json.dump({**stats, "elapsed_sec": round(elapsed, 1),
               "time_str": f"{h}h{m}m{s}s",
               "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())},
              open(base / "download_summary.json", "w"), indent=2)


if __name__ == "__main__":
    main()
