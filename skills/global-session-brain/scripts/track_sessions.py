#!/usr/bin/env python3
"""
Session tracker for global-session-brain.

Lists unprocessed sessions, marks them as processed after extraction.
Manifest stored at ~/.hermes/brain/.brain_manifest.json

Usage:
    python3 track_sessions.py --list-new           # List unprocessed sessions
    python3 track_sessions.py --list-new --since 2h # Only recent
    python3 track_sessions.py --mark-done SESSION_ID  # Mark as processed
    python3 track_sessions.py --stats               # Show stats
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def get_brain_dir():
    """Resolve brain directory from HERMES_HOME or default."""
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    return Path(hermes_home) / "brain"


def get_manifest_path():
    return get_brain_dir() / ".brain_manifest.json"


def load_manifest():
    """Load the brain manifest. Returns {'processed': {'session_id': date_processed}}."""
    path = get_manifest_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"processed": {}, "last_extraction": None, "total_extracted_files": 0}


def save_manifest(manifest):
    path = get_manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)


def list_session_files():
    """Return list of session JSON files sorted by modification time (newest first)."""
    sessions_dir = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "sessions"
    if not sessions_dir.exists():
        return []
    
    files = []
    for f in sessions_dir.glob("session_*.json"):
        if f.is_file():
            stat = f.stat()
            files.append({
                "path": str(f),
                "session_id": f.stem,
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            })
    
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files


def parse_since(since_str: str) -> float:
    """Parse '--since' value like '2h', '30m', '1d' into seconds."""
    if since_str.endswith("h"):
        return float(since_str[:-1]) * 3600
    elif since_str.endswith("m"):
        return float(since_str[:-1]) * 60
    elif since_str.endswith("d"):
        return float(since_str[:-1]) * 86400
    raise ValueError(f"Unsupported since format: {since_str}")


def cmd_list_new(since: str = None):
    """List sessions not yet processed."""
    manifest = load_manifest()
    sessions = list_session_files()
    
    processed = set(manifest.get("processed", {}).keys())
    now = datetime.now(timezone.utc).timestamp()
    
    cutoff = None
    if since:
        cutoff = now - parse_since(since)
    
    new_sessions = []
    for s in sessions:
        if s["session_id"] in processed:
            continue
        if cutoff and s["mtime"] < cutoff:
            continue
        new_sessions.append(s)
    
    output = {
        "new_sessions": new_sessions,
        "count": len(new_sessions),
        "total_sessions": len(sessions),
        "processed_count": len(processed),
    }
    print(json.dumps(output, indent=2))
    return output


def cmd_mark_done(session_ids: list[str]):
    """Mark sessions as processed in the manifest."""
    manifest = load_manifest()
    now = datetime.now(timezone.utc).isoformat()
    
    for sid in session_ids:
        manifest["processed"][sid] = now
    
    manifest["last_extraction"] = now
    save_manifest(manifest)
    print(json.dumps({
        "marked": session_ids,
        "total_processed": len(manifest["processed"]),
    }))


def cmd_stats():
    """Show brain statistics."""
    manifest = load_manifest()
    sessions = list_session_files()
    wiki_dir = get_brain_dir() / "wiki"
    
    wiki_files = []
    if wiki_dir.exists():
        wiki_files = list(wiki_dir.rglob("*.md"))
    
    graph_path = get_brain_dir() / "graphify-out" / "graph.json"
    graph_nodes = 0
    graph_edges = 0
    if graph_path.exists():
        try:
            import networkx as nx
            from networkx.readwrite import json_graph
            with open(graph_path) as f:
                G = json_graph.node_link_graph(json.load(f), edges="links")
            graph_nodes = G.number_of_nodes()
            graph_edges = G.number_of_edges()
        except Exception:
            pass
    
    stats = {
        "sessions": {
            "total": len(sessions),
            "processed": len(manifest.get("processed", {})),
            "unprocessed": len(sessions) - len(manifest.get("processed", {})),
        },
        "wiki": {
            "files": len(wiki_files),
            "total_size": sum(f.stat().st_size for f in wiki_files if f.is_file()),
        },
        "graph": {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "exists": graph_path.exists(),
        },
        "last_extraction": manifest.get("last_extraction"),
    }
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Session tracker for global-session-brain")
    parser.add_argument("--list-new", action="store_true", help="List unprocessed sessions")
    parser.add_argument("--since", type=str, help="Only sessions since (e.g., 2h, 30m, 1d)")
    parser.add_argument("--mark-done", nargs="+", help="Mark session IDs as processed")
    parser.add_argument("--stats", action="store_true", help="Show brain statistics")
    
    args = parser.parse_args()
    
    if args.list_new:
        cmd_list_new(since=args.since)
    elif args.mark_done:
        cmd_mark_done(args.mark_done)
    elif args.stats:
        cmd_stats()
    else:
        # Default: show stats
        cmd_stats()
