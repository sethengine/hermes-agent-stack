#!/usr/bin/env python3
"""
multi-angle-search.py — Multi-angle search + extract + summarize pipeline.

Searches a topic from multiple angles (overview, technical, community, critical),
extracts content from top results, and produces a structured summary.

Usage:
    python3 multi-angle-search.py <topic> [--limit N] [--depth quick|moderate|deep]
    
Examples:
    python3 multi-angle-search.py "RAG with knowledge graphs" 
    python3 multi-angle-search.py "MQTT vs gRPC for IoT" --depth deep --limit 10
"""

import sys
import argparse
from hermes_tools import web_search, web_extract


def search_angle(topic, query_template, angle_name, limit=3):
    """Run a search for one angle and return results."""
    query = query_template.format(topic=topic)
    print(f"  🔍 [{angle_name}] Searching: {query}")
    results = web_search(query, limit=limit)
    
    hits = []
    if isinstance(results, dict) and "data" in results:
        items = results["data"].get("web", [])
        for item in items[:limit]:
            hits.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
            })
            print(f"    → {item.get('title', 'Untitled')[:80]}")
    return hits


def extract_content(urls, max_chars=2000):
    """Extract content from URLs and return truncated text."""
    extracted = []
    for url in urls:
        try:
            content = web_extract(urls=[url])
            if isinstance(content, dict) and "results" in content:
                for r in content["results"]:
                    text = r.get("content", "")[:max_chars]
                    extracted.append({"url": url, "content": text})
        except Exception as e:
            extracted.append({"url": url, "content": f"[Extraction failed: {e}]"})
    return extracted


def main():
    parser = argparse.ArgumentParser(
        description="Multi-angle research search + extract pipeline"
    )
    parser.add_argument("topic", help="Research topic")
    parser.add_argument(
        "--limit", type=int, default=3,
        help="Results per angle (default: 3)"
    )
    parser.add_argument(
        "--depth", choices=["quick", "moderate", "deep"], default="moderate",
        help="Research depth (default: moderate)"
    )
    parser.add_argument(
        "--search-only", action="store_true",
        help="Only search, don't extract content"
    )
    
    args = parser.parse_args()
    topic = args.topic
    limit = args.limit
    
    # Define search angles based on depth
    angles = [
        ("Overview", "{topic} overview 2025 explained"),
        ("Technical", "{topic} architecture implementation guide"),
        ("Community", "{topic} reddit discussion experience"),
        ("Critical", "{topic} limitations problems issues alternatives"),
    ]
    
    if args.depth == "quick":
        angles = angles[:2]  # Overview + Technical only
    elif args.depth == "deep":
        angles.append(("Latest", "{topic} 2025 update new developments"))
        angles.append(("Comparison", "{topic} vs comparison benchmark"))
    
    print(f"\n{'='*60}")
    print(f"  Multi-Angle Research: {topic}")
    print(f"  Depth: {args.depth.upper()} | {len(angles)} angles")
    print(f"{'='*60}\n")
    
    # Phase 1: Search all angles
    all_urls = []
    for angle_name, query_template in angles:
        hits = search_angle(topic, query_template, angle_name, limit)
        all_urls.extend([h["url"] for h in hits if h["url"]])
        print()
    
    # Phase 2: Extract (if not search-only)
    if not args.search_only and all_urls:
        # Deduplicate URLs
        unique_urls = list(dict.fromkeys(all_urls))[:10]
        
        print(f"\n{'='*60}")
        print(f"  Phase 2: Extracting content from {len(unique_urls)} sources")
        print(f"{'='*60}\n")
        
        contents = extract_content(unique_urls)
    
    # Phase 3: Summary
    print(f"\n{'='*60}")
    print(f"  Research Complete")
    print(f"{'='*60}")
    print(f"  Topic:     {topic}")
    print(f"  Angles:    {len(angles)}")
    print(f"  Sources:   {len(all_urls)} discovered, {len(set(all_urls))} unique")
    print(f"  Depth:     {args.depth}")
    print()
    print(f"  Next steps:")
    print(f"    1. Review the extracted content from each angle")
    print(f"    2. Cross-reference claims across angles")
    print(f"    3. Fill gaps with targeted follow-up searches")
    print(f"    4. Synthesize into research report")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
