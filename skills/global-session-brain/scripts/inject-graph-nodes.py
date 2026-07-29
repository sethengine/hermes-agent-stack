#!/usr/bin/env python3
"""
inject-graph-nodes.py — Add new document nodes + links to an existing graph.json,
then optionally re-cluster.

Usage:
    python3 inject-graph-nodes.py <graph_path> <nodes_json> [links_json] [--cluster-dir DIR]

Args:
    graph_path    Path to existing graph.json (e.g. ~/.hermes/brain/graphify-out/graph.json)
    nodes_json    JSON string or file path containing new nodes array
    links_json    Optional JSON string or file path containing new links array
    --cluster-dir DIR   If set, run graphify cluster-only on DIR after injection

Input format (nodes):
    [
      {
        "id": "my_new_node_document",
        "label": "My New Node Label",
        "file_type": "document",
        "source_file": "category/my-file.md",
        "source_location": null,
        "source_url": null,
        "captured_at": "2026-06-13T00:00:00+00:00",
        "author": null,
        "contributor": null,
        "community": 0,
        "norm_label": "my new node label normalized"
      },
      ...
    ]

Input format (links):
    [
      {
        "relation": "references",
        "confidence": "EXTRACTED",
        "confidence_score": 1.0,
        "source_file": "category/my-file.md",
        "weight": 1.0,
        "source_location": null,
        "_src": "my_new_node_document",
        "_tgt": "existing_target_node",
        "source": "my_new_node_document",
        "target": "existing_target_node"
      },
      ...
    ]

Notes:
  - Only file_type values accepted by graphify: code, document, image, paper, rationale.
    All other types are silently coerced to 'document'.
  - Duplicate node IDs and duplicate links are skipped (idempotent).
  - Existing graph data (other nodes, links) is preserved.
"""
import json, sys, os, subprocess
from pathlib import Path

VALID_TYPES = {'code', 'document', 'image', 'paper', 'rationale'}


def load_json(source: str):
    """Load JSON from a file path or inline string."""
    source = source.strip()
    if source.startswith('[') or source.startswith('{'):
        return json.loads(source)
    path = Path(source)
    if path.exists():
        return json.loads(path.read_text())
    raise ValueError(f"Could not parse JSON input: not a valid file path or JSON string")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    graph_path = Path(sys.argv[1])
    nodes_input = sys.argv[2]
    links_input = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else None
    cluster_dir = None

    for i, arg in enumerate(sys.argv):
        if arg == '--cluster-dir' and i + 1 < len(sys.argv):
            cluster_dir = sys.argv[i + 1]

    if not graph_path.exists():
        print(f"Error: graph.json not found at {graph_path}", file=sys.stderr)
        sys.exit(1)

    # Load existing graph
    with open(graph_path) as f:
        graph = json.load(f)

    # Load new nodes
    new_nodes = load_json(nodes_input)
    if isinstance(new_nodes, dict):
        new_nodes = [new_nodes]

    # Validate and coerce node types
    for node in new_nodes:
        ft = node.get('file_type', 'document')
        if ft not in VALID_TYPES:
            node['file_type'] = 'document'

    # Merge nodes (skip duplicates by id)
    existing_ids = {n['id'] for n in graph['nodes']}
    added_nodes = 0
    for node in new_nodes:
        if node['id'] not in existing_ids:
            graph['nodes'].append(node)
            existing_ids.add(node['id'])
            added_nodes += 1

    # Merge links (skip duplicates by source+target+relation)
    existing_links = set()
    for link in graph.get('links', []):
        existing_links.add((link.get('source'), link.get('target'), link.get('relation')))
    added_links = 0
    if links_input:
        new_links = load_json(links_input)
        if isinstance(new_links, dict):
            new_links = [new_links]
        for link in new_links:
            key = (link.get('source'), link.get('target'), link.get('relation'))
            if key not in existing_links:
                graph.setdefault('links', []).append(link)
                existing_links.add(key)
                added_links += 1

    # Write updated graph
    with open(graph_path, 'w') as f:
        json.dump(graph, f, indent=2)

    print(f"Injected {added_nodes} nodes and {added_links} links into {graph_path}")
    print(f"  Graph now: {len(graph['nodes'])} nodes, {len(graph.get('links', []))} links")

    # Re-cluster if requested
    if cluster_dir:
        cluster_path = Path(cluster_dir).resolve()
        print(f"Re-clustering via graphify cluster-only {cluster_path}...")
        result = subprocess.run(
            ['graphify', 'cluster-only', str(cluster_path)],
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"Cluster warning/stderr: {result.stderr}", file=sys.stderr)
        else:
            print("Re-clustering complete.")

    return added_nodes, added_links


if __name__ == '__main__':
    main()
