#!/usr/bin/env python3
"""
verify-and-fix-link-directions.py

Verify that injected links in graph.json have the correct source→target
direction after 'graphify cluster-only' has been run. Fix any that were
reversed by cluster-only (a known graphify bug).

Usage:
    # Verify only (dry-run):
    python3 verify-and-fix-link-directions.py graph.json new_links.json

    # Verify and fix (remove reversed links, re-add with correct direction):
    python3 verify-and-fix-link-directions.py graph.json new_links.json --fix

    # Verify only, verbose output with per-link details:
    python3 verify-and-fix-link-directions.py graph.json new_links.json --verbose

The script checks every link in new_links.json against the current graph.
cluster-only reverses direction for cross-boundary links (newly injected →
pre-existing), but leaves new→new links intact. This script detects both cases.

Exit codes:
    0 — All links correct (or fixed successfully with --fix)
    1 — One or more links reversed (--fix not applied) or errors occurred
"""

import json
import sys
import copy


def load_json(path: str) -> list | dict:
    """Load JSON from file. Wraps single dicts in a list for compatibility."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        # inject-graph-nodes.py uses this pattern: load_json() wraps dicts.
        # But for links we need a list, so only wrap non-dict-keyed structures.
        # Here we assume the file is always a list of link objects as written by the agent.
        return data
    return data


def verify_links(graph_path: str, links_path: str, fix: bool = False, verbose: bool = False) -> bool:
    """Verify link directions. Returns True if all correct or fixed."""
    with open(graph_path) as f:
        graph = json.load(f)

    with open(links_path) as f:
        injected = json.load(f)

    if isinstance(injected, dict):
        print(f"ERROR: {links_path} is a dict, not a list. "
              f"Inject-graph-nodes.py expects separate JSON arrays. "
              f"See skill pitfall: 'Script input format: separate files'",
              file=sys.stderr)
        return False

    fixed_links = []
    reversed_count = 0
    correct_count = 0
    missing_count = 0

    for link in injected:
        expected_src = link.get('source')
        expected_tgt = link.get('target')
        rel = link.get('relation', '?')

        if not expected_src or not expected_tgt:
            print(f"WARNING: Link missing source or target: {link.get('source', '?')} → {link.get('target', '?')} ({rel})")
            continue

        # Check both directions in the graph
        correct_direction = [
            l for l in graph['links']
            if l.get('source') == expected_src and l.get('target') == expected_tgt
        ]
        reversed_direction = [
            l for l in graph['links']
            if l.get('source') == expected_tgt and l.get('target') == expected_src
        ]

        if correct_direction:
            correct_count += 1
            if verbose:
                print(f"  ✓  {expected_src} → {expected_tgt}  ({rel})")
        elif reversed_direction:
            reversed_count += 1
            print(f"  ✗  REVERSED: {expected_tgt} → {expected_src}  ({rel})  [was {expected_src} → {expected_tgt}]")
            if fix:
                # Record the corrected link
                corrected = copy.deepcopy(reversed_direction[0])
                corrected['source'] = expected_src
                corrected['target'] = expected_tgt
                fixed_links.append(corrected)
        else:
            missing_count += 1
            print(f"  ?  MISSING:  {expected_src} → {expected_tgt}  ({rel}) — no matching link found in either direction")
            if fix:
                # Create a new link entry from scratch
                corrected = {
                    "source": expected_src,
                    "target": expected_tgt,
                    "relation": rel,
                    "source_file": link.get("source_file", ""),
                    "confidence": link.get("confidence", "DECLARED"),
                    "confidence_score": link.get("confidence_score", 0.8),
                    "weight": link.get("weight", 1.0),
                    "source_location": link.get("source_location", None)
                }
                fixed_links.append(corrected)

    # Summary
    total = correct_count + reversed_count + missing_count
    print(f"\nSummary: {total} links checked — "
          f"{correct_count} correct, {reversed_count} reversed, {missing_count} missing")

    if reversed_count == 0 and missing_count == 0:
        print("✓ All links correct. No fix needed.")
        return True

    if not fix:
        action = ["--fix"] if reversed_count or missing_count else []
        print(f"\n⚠  Run with --fix to correct {reversed_count} reversed link(s) and add {missing_count} missing link(s)")
        return reversed_count == 0 and missing_count == 0

    # Apply fixes
    if reversed_count or missing_count:
        # Build set of reversed (source, target, relation) triples to remove.
        # Using relation in the key is CRITICAL: when two links exist between the same
        # pair of nodes (e.g., A→B with conceptually_related_to AND B→A with depends_on),
        # filtering by (source,target) alone would destroy the correctly-oriented link
        # alongside the reversed one. Relation disambiguates.
        reversed_triples = set()
        for link in injected:
            expected_src = link.get('source')
            expected_tgt = link.get('target')
            rel = link.get('relation')
            if expected_src and expected_tgt:
                has_reversed = any(
                    l.get('source') == expected_tgt and l.get('target') == expected_src
                    for l in graph['links']
                )
                if has_reversed:
                    reversed_triples.add((expected_tgt, expected_src, rel))
                # for missing links, we just add them back

        # Remove reversed links (relation-aware — only removes the specific link)
        original_count = len(graph['links'])
        graph['links'] = [
            l for l in graph['links']
            if (l.get('source'), l.get('target'), l.get('relation')) not in reversed_triples
        ]
        removed = original_count - len(graph['links'])
        print(f"Removed {removed} reversed link(s)")

        # Add corrected links
        graph['links'].extend(fixed_links)
        print(f"Added {len(fixed_links)} corrected link(s)")

        # Save
        with open(graph_path, 'w') as f:
            json.dump(graph, f, indent=2)

        print(f"\n✓ Fixed. Graph now: {len(graph['nodes'])} nodes, {len(graph['links'])} links")

        # One final check
        all_ok = True
        for link in injected:
            expected_src = link.get('source')
            expected_tgt = link.get('target')
            if expected_src and expected_tgt:
                found = any(
                    l.get('source') == expected_src and l.get('target') == expected_tgt
                    for l in graph['links']
                )
                if not found:
                    print(f"  ✗  STILL MISSING after fix: {expected_src} → {expected_tgt}")
                    all_ok = False
        if all_ok:
            print(f"✓ Post-fix verification: all {len(injected)} links present with correct direction")
        return all_ok

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Verify and optionally fix link directions in graph.json after cluster-only injection."
    )
    parser.add_argument("graph_path", help="Path to graph.json")
    parser.add_argument("links_path", help="Path to the injected new_links.json")
    parser.add_argument("--fix", action="store_true", help="Apply fixes (remove reversed, add correct directions)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detailed per-link output")
    args = parser.parse_args()

    success = verify_links(args.graph_path, args.links_path, fix=args.fix, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
