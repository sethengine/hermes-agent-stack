#!/usr/bin/env python3
"""
MCP stdio server skeleton — copy and customize for a new Hermes MCP bridge.

HOW TO CUSTOMIZE:
1. Rename TOOLS with your tool definitions
2. Fill in the handle_* functions with your logic
3. Set SERVER_NAME and SERVER_VERSION
4. Optionally: add SEARXNG_MCP_DEBUG-style debug toggle
"""

import json
import sys

SERVER_NAME = "my-custom-server"
SERVER_VERSION = "1.0.0"

# ── Tool Definitions ────────────────────────────────────────────────────
# Each tool needs: name, description, inputSchema (JSON Schema)

TOOLS = [
    {
        "name": "my_tool",
        "description": "What this tool does — shown to the agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query parameter",
                },
            },
            "required": ["query"],
        },
    },
]

# ── Your Tool Logic ─────────────────────────────────────────────────────
# Replace these with your actual implementation


def handle_my_tool(args: dict) -> str:
    """Process a tool call and return the result text."""
    query = args.get("query", "")
    # Your logic here
    return f"Result for: {query}"


def handle_initialize() -> dict:
    """Return the InitializeResult."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


# ── MCP JSON-RPC Framework ──────────────────────────────────────────────
# Don't modify below this line unless you know what you're doing.


def make_response(req_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result})


def make_error(req_id, code, message):
    return json.dumps(
        {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    )


def text_content(text: str) -> dict:
    """Wrap text in MCP tool result format."""
    return {"content": [{"type": "text", "text": text}]}


def handle_request(msg: dict) -> str | None:
    """Route JSON-RPC messages to handlers."""
    req_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if method == "initialize":
        return make_response(req_id, handle_initialize())

    elif method == "tools/list":
        return make_response(req_id, {"tools": TOOLS})

    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        # ── Route tool calls ──────────────────────────
        if name == "my_tool":
            result = handle_my_tool(args)
            return make_response(req_id, text_content(result))

        # Add more elif branches for additional tools

        return make_error(req_id, -32601, f"Unknown tool: {name}")

    elif method == "ping":
        return make_response(req_id, {})

    elif method == "notifications/initialized":
        return None  # Notifications get no response

    elif method.startswith("notifications/"):
        return None  # Silently ignore other notifications

    return make_error(req_id, -32601, f"Unknown method: {method}")


def main():
    """Read JSON-RPC messages from stdin, write responses to stdout."""
    buffer = ""
    for line in sys.stdin:
        if not line.strip():
            continue
        buffer += line
        try:
            msg = json.loads(buffer)
            buffer = ""
        except json.JSONDecodeError:
            # JSON spans multiple lines (shouldn't happen with minified
            # JSON, but handles edge cases)
            continue

        if not isinstance(msg, dict):
            continue

        try:
            resp = handle_request(msg)
        except Exception as e:
            resp = make_error(msg.get("id"), -32603, f"Internal error: {e}")

        if resp is not None:
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
