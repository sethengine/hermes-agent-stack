#!/usr/bin/env python3
"""
find-related-nodes.py — Search a graph.json for nodes matching keywords.

Replaces the ad-hoc inline Python snippet in the brain extraction pipeline's
"find existing nodes to link to" step. Searches both node IDs and labels
with case-insensitive substring match + optional fuzzy ratio.

Usage:
    python3 find-related-nodes.py "doom emacs keybindings"
    python3 find-related-nodes.py "pipewire" "nvidia" "latency" --fuzzy 70
    python3 find-related-nodes.py --all                        # dump all nodes
    python3 find-related-nodes.py --graph /custom/path/graph.json "keyword"

Args:
    keywords       One or more search terms. Results match if any keyword appears.
                   Matching is case-insensitive substring on both id and label.
    --graph PATH   Path to graph.json (default: ~/.hermes/brain/graphify-out/graph.json)
    --fuzzy N      Enable fuzzy matching with minimum similarity ratio 0-N (e.g., 70)
    --all          List every node in the graph (no filtering).
    --count        Only show match count, not individual nodes.
    --fields F1,F2 Comma-separated fields to search (default: id,label).
                   Options: id, label, community, file_type, metadata.path
    --format       Output format: 'table' (default), 'json', or 'ids-only'.
    --help, -h   Show this usage message and exit.
    --sort FIELD   Sort results by a field (id, label, community, file_type).
                   Default: relevance order (matches label first).

Output:
    By default, a table with: ID | Label | Type | Community | MatchOn
    With --format json: JSON array of matched node objects.
    With --format ids-only: one ID per line (for piping into other tools).
    Exit code 0 if matches found, 1 if none.
"""

import json, sys, os, difflib
from pathlib import Path

DEFAULT_GRAPH = os.path.expanduser("~/.hermes/brain/graphify-out/graph.json")
VALID_FIELDS = {"id", "label", "community", "file_type", "metadata.path"}


def load_graph(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Error: graph.json not found at {p}", file=sys.stderr)
        sys.exit(2)
    with open(p) as f:
        return json.load(f)


def get_field_value(node: dict, field: str) -> str:
    """Extract a field value from a node, supporting dot-notation like metadata.path."""
    if "." in field:
        parts = field.split(".")
        val = node
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part, "")
            else:
                return ""
        return str(val) if val else ""
    return str(node.get(field, ""))


def matches_keyword(node: dict, keyword: str, fields: list[str], fuzzy: int = 0) -> tuple[bool, str]:
    """Check if node matches keyword. Returns (matched, field_that_matched)."""
    kw_lower = keyword.lower().strip()
    for field in fields:
        val = get_field_value(node, field).lower()
        if kw_lower in val:
            return True, field
        if fuzzy > 0:
            ratio = difflib.SequenceMatcher(None, kw_lower, val).ratio() * 100
            if ratio >= fuzzy:
                return True, f"{field}(fuzzy:{ratio:.0f}%)"
    return False, ""


def format_table(results: list[dict]) -> str:
    """Format results as a table."""
    if not results:
        return "No matches found."

    rows = []
    for r in results:
        rows.append({
            "id": r["node"]["id"],
            "label": r["node"].get("label", "")[:60],
            "type": r["node"].get("file_type", "?"),
            "community": str(r["node"].get("community", "?")),
            "match": r["matched_on"],
        })

    # Column widths
    id_w = max(len(r["id"]) for r in rows + [{"id": "ID"}])
    lb_w = max(len(r["label"]) for r in rows + [{"label": "Label"}])
    ty_w = max(len(r["type"]) for r in rows + [{"type": "Type"}])
    cm_w = max(len(r["community"]) for r in rows + [{"community": "Comm"}])
    mt_w = max(len(r["match"]) for r in rows + [{"match": "MatchOn"}])

    sep = f"+{'-'*(id_w+2)}+{'-'*(lb_w+2)}+{'-'*(ty_w+2)}+{'-'*(cm_w+2)}+{'-'*(mt_w+2)}+"
    hdr = f"| {'ID':<{id_w}} | {'Label':<{lb_w}} | {'Type':<{ty_w}} | {'Comm':<{cm_w}} | {'MatchOn':<{mt_w}} |"

    lines = [sep, hdr, sep]
    for r in rows:
        lines.append(
            f"| {r['id']:<{id_w}} | {r['label']:<{lb_w}} | {r['type']:<{ty_w}} | "
            f"{r['community']:<{cm_w}} | {r['match']:<{mt_w}} |"
        )
    lines.append(sep)
    lines.append(f"\n{len(rows)} match(es)")
    return "\n".join(lines)


def main():
    keywords = []
    graph_path = DEFAULT_GRAPH
    fuzzy = 0
    show_all = False
    count_only = False
    fields = ["id", "label"]
    fmt = "table"
    sort_field = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--graph" and i + 1 < len(args):
            graph_path = args[i + 1]
            i += 2
        elif a == "--fuzzy" and i + 1 < len(args):
            fuzzy = int(args[i + 1])
            i += 2
        elif a == "--all":
            show_all = True
            i += 1
        elif a == "--count":
            count_only = True
            i += 1
        elif a == "--fields" and i + 1 < len(args):
            fields = [f.strip() for f in args[i + 1].split(",")]
            for f in fields:
                if f not in VALID_FIELDS:
                    print(f"Warning: unknown field '{f}'. Valid: {', '.join(sorted(VALID_FIELDS))}", file=sys.stderr)
            i += 2
        elif a == "--format" and i + 1 < len(args):
            fmt = args[i + 1]
            if fmt not in ("table", "json", "ids-only"):
                print(f"Error: unknown format '{fmt}'. Use table, json, or ids-only.", file=sys.stderr)
                sys.exit(2)
            i += 2
        elif a == "--sort" and i + 1 < len(args):
            sort_field = args[i + 1]
            if sort_field not in VALID_FIELDS:
                print(f"Error: unknown sort field '{sort_field}'. Valid: {', '.join(sorted(VALID_FIELDS))}", file=sys.stderr)
                sys.exit(2)
            i += 2
        elif a in ("-h", "--help"):
            print(__doc__.strip())
            sys.exit(0)
        elif a.startswith("--"):
            print(f"Error: unknown option '{a}'. Use --help for usage.", file=sys.stderr)
            sys.exit(2)
        else:
            keywords.append(a)
            i += 1

    graph = load_graph(graph_path)
    nodes = graph.get("nodes", [])

    if show_all:
        results = [{"node": n, "matched_on": "--"} for n in nodes]
    else:
        if not keywords:
            print("Error: provide at least one keyword or --all", file=sys.stderr)
            sys.exit(2)
        results = []
        for node in nodes:
            for kw in keywords:
                matched, on_field = matches_keyword(node, kw, fields, fuzzy)
                if matched:
                    results.append({"node": node, "matched_on": on_field})
                    break

    if sort_field:
        results.sort(key=lambda r: get_field_value(r["node"], sort_field).lower())

    if count_only:
        print(len(results))
        sys.exit(0 if results else 1)

    if fmt == "json":
        print(json.dumps([r["node"] for r in results], indent=2))
    elif fmt == "ids-only":
        for r in results:
            print(r["node"]["id"])
    else:
        print(format_table(results))

    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
