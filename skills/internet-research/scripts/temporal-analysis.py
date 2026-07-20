#!/usr/bin/env python3
"""
temporal-analysis.py — Search a topic year-by-year and build a timeline.

Shows how understanding of a topic evolved over time.
Useful for technology tracking, policy changes, or narrative analysis.

Usage:
    python3 temporal-analysis.py <topic> [--start YEAR] [--end YEAR]
    
Examples:
    python3 temporal-analysis.py "retrieval augmented generation" --start 2020
    python3 temporal-analysis.py "EU AI Act" --start 2021 --end 2025
"""

import sys
import argparse
from hermes_tools import web_search


def search_year(topic, year, limit=3):
    """Search for a topic in a specific year."""
    query = f"{topic} {year}"
    try:
        results = web_search(query, limit=limit)
        hits = []
        if isinstance(results, dict) and "data" in results:
            items = results["data"].get("web", [])
            for item in items[:limit]:
                hits.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                })
        return hits
    except Exception as e:
        print(f"    [Error: {e}]")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Year-by-year temporal analysis of a topic"
    )
    parser.add_argument("topic", help="Topic to analyze temporally")
    parser.add_argument(
        "--start", type=int, default=2020,
        help="Start year (default: 2020)"
    )
    parser.add_argument(
        "--end", type=int, default=2025,
        help="End year (default: 2025)"
    )
    parser.add_argument(
        "--limit", type=int, default=3,
        help="Results per year (default: 3)"
    )
    
    args = parser.parse_args()
    topic = args.topic
    start = args.start
    end = args.end
    limit = args.limit
    
    years = list(range(start, end + 1))
    
    print(f"\n{'='*60}")
    print(f"  Temporal Analysis: {topic}")
    print(f"  Period: {start} – {end} ({len(years)} years)")
    print(f"{'='*60}\n")
    
    timeline = []
    
    for year in years:
        print(f"  📅 {year}")
        hits = search_year(topic, year, limit)
        
        for hit in hits:
            title = hit.get("title", "Untitled")[:100]
            print(f"    • {title}")
        
        timeline.append({"year": year, "hits": hits})
        print()
    
    # Summary
    print(f"{'='*60}")
    print(f"  Timeline Summary")
    print(f"{'='*60}")
    
    for entry in timeline:
        hits = entry["hits"]
        key_titles = [h["title"][:80] for h in hits[:2]]
        print(f"  {entry['year']}: {len(hits)} results")
        if key_titles:
            print(f"    Key: {key_titles[0]}")
    
    print()
    print(f"  Observations:")
    print(f"    • Total sources found: {sum(len(t['hits']) for t in timeline)}")
    print(f"    • Years with most results: ", end="")
    max_hits = max(len(t["hits"]) for t in timeline)
    peak_years = [str(t["year"]) for t in timeline if len(t["hits"]) == max_hits]
    print(", ".join(peak_years))
    print()
    print(f"  Next steps:")
    print(f"    1. Extract content from key sources in peak years")
    print(f"    2. Identify inflection points between years")
    print(f"    3. Look for paradigm shifts in how the topic was discussed")
    print(f"    4. Synthesize into a narrative timeline")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
