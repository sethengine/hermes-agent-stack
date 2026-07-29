#!/usr/bin/env python3
"""
source-credibility-check.py — Quick credibility assessment for a URL or domain.

Usage:
    python3 source-credibility-check.py <url_or_domain>
    
Outputs a credibility rating and explanation.
"""

import sys
import re
from urllib.parse import urlparse

# ── Trusted domains (primary sources, official, peer-reviewed) ──
TRUSTED_DOMAINS = {
    # Academic / Research
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "ieeexplore.ieee.org",
    "dl.acm.org", "semanticscholar.org", "scholar.google.com",
    "nature.com", "science.org", "cell.com", "thelancet.com",
    "nejm.org", "bmj.com", "plos.org", "frontiersin.org",
    "jmlr.org", "neurips.cc", "icml.cc", "openreview.net",
    "aclweb.org", "naacl.org", "emnlp.org",
    
    # Government
    ".gov", ".mil", "who.int", "cdc.gov", "nih.gov", "nsf.gov",
    "nasa.gov", "europa.eu", "congress.gov", "parliament.uk",
    "gov.uk", "cisa.gov", "nist.gov",
    
    # Major news (wire services & established outlets)
    "reuters.com", "ap.org", "apnews.com", "bloomberg.com",
    "wsj.com", "nytimes.com", "economist.com", "ft.com",
    "theguardian.com", "bbc.com", "bbc.co.uk", "npr.org",
    "pbs.org", "newyorker.com", "washingtonpost.com",
    
    # Technical / Standards
    "ietf.org", "rfc-editor.org", "w3.org", "whatwg.org",
    "mdn.mozilla.org", "developer.mozilla.org",
    "kernel.org", "debian.org", "gnu.org",
    "python.org", "pypi.org", "npmjs.com", "crates.io",
    "docker.com", "kubernetes.io", "git-scm.com",
    "github.com", "gitlab.com",
    
    # Educational
    ".edu", "stanford.edu", "mit.edu", "cam.ac.uk", "ox.ac.uk",
    "berkeley.edu", "cmu.edu", "harvard.edu",
}

# ── Suspicious / Low-credibility domains ──
SUSPICIOUS_DOMAINS = {
    "dailymail.co.uk", "infowars.com", "breitbart.com",
    "zerohedge.com", "naturalnews.com", "beforeitsnews.com",
    "wnd.com", "truthout.org", "theonion.com",  # satire, not news
    "worldstar.com", "buzzfeed.com",  # tabloid/entertainment
}

# ── Content farms / AI-generated content signals ──
CONTENT_FARM_PATTERNS = [
    r"medium\.com/@.+",  # personal Medium accounts (some are good, many are not)
    r"dev\.to/.+",       # dev.to personal blogs
    r"hashnode\.dev/.+",
    r"substack\.com/@.+",
    r"newsletter\.+.substack\.com",
]

CREDIBILITY_EXPLANATIONS = {
    "trusted": (
        "Trusted source — authoritative domain with editorial standards, "
        "peer review, or official status."
    ),
    "suspicious": (
        "Low-credibility source — known for misinformation, sensationalism, "
        "or lack of editorial standards. Verify all claims independently."
    ),
    "content_farm": (
        "Likely content farm or AI-generated blog — may contain factual errors. "
        "Check author credentials and cross-reference claims."
    ),
    "academic": (
        "Academic / research source — peer-reviewed. Check publication date "
        "and whether findings have been reproduced."
    ),
    "unknown": (
        "Unknown or unverified source. Check: who runs this site? What's their "
        "editorial process? When was this published? Are claims sourced?"
    ),
}


def classify_domain(domain):
    """Classify a domain into a credibility category."""
    domain_lower = domain.lower()
    
    # Check for trusted TLDs first (some domains like .gov, .edu don't match the set)
    if domain_lower.endswith(".gov") or domain_lower.endswith(".mil"):
        return "trusted"
    if domain_lower.endswith(".edu"):
        return "academic"
    
    # Check trusted domains
    for trusted in TRUSTED_DOMAINS:
        if trusted.startswith("."):
            if domain_lower.endswith(trusted):
                return "trusted"
        elif trusted == domain_lower or domain_lower.endswith("." + trusted):
            return "trusted"
    
    # Check suspicious domains
    for suspicious in SUSPICIOUS_DOMAINS:
        if suspicious == domain_lower or domain_lower.endswith("." + suspicious):
            return "suspicious"
    
    # Check content farm patterns
    for pattern in CONTENT_FARM_PATTERNS:
        full = domain_lower + "/"  # Add trailing slash for path matching
        if re.search(pattern, full):
            return "content_farm"
    
    return "unknown"


def get_page_age_indicator(domain):
    """Return freshness guidance based on domain type."""
    tech_domains = {
        "github.com", "pypi.org", "npmjs.com", "crates.io",
        "docs.docker.com", "kubernetes.io",
    }
    
    fast_moving = {
        "github.com", "medium.com", "dev.to", "arxiv.org",
        "reddit.com", "stackoverflow.com",
    }
    
    if domain in fast_moving or any(d in domain for d in [".github.io", "blogspot"]):
        return "Fast-moving — prefer content < 6 months old"
    if domain in tech_domains:
        return "Tech — prefer content < 1 year old"
    return "Standard — check publication date"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 source-credibility-check.py <url_or_domain>")
        sys.exit(1)
    
    raw = sys.argv[1].strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    
    parsed = urlparse(raw)
    domain = parsed.netloc or parsed.path
    
    category = classify_domain(domain)
    
    # Emoji rating
    ratings = {
        "trusted": "🟢",
        "academic": "🟢",
        "unknown": "🟡",
        "content_farm": "🟠",
        "suspicious": "🔴",
    }
    
    print(f"{'='*60}")
    print(f"  Source Credibility Check")
    print(f"{'='*60}")
    print(f"  URL:      {raw}")
    print(f"  Domain:   {domain}")
    print(f"  Rating:   {ratings.get(category, '❓')} {category.upper()}")
    print()
    print(f"  Assessment:")
    print(f"    {CREDIBILITY_EXPLANATIONS.get(category, 'Unknown category')}")
    print()
    print(f"  Freshness:")
    print(f"    {get_page_age_indicator(domain)}")
    print(f"{'='*60}")
    
    if category in ("suspicious", "content_farm"):
        print(f"  ⚠️  EXERCISE CAUTION — verify all claims from this source")
        print(f"     against at least one independent primary source.")
    elif category == "unknown":
        print(f"  ℹ️  Verify authorship, editorial process, and publication date.")
        print(f"     Cross-reference key claims with known-reliable sources.")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
