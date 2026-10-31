"""
trip_09_mcp_client_demo.py
──────────────────────────
Lesson 09 · MCP Client: connect, handshake, list tools, and call each one.

The story
    trip_08 is the server — it owns the DB, the knowledge base, and the tools.
    This file is the CLIENT. It knows nothing about SQLite or ChromaDB.
    It connects to the server, asks "what tools do you have?", gets the list,
    and calls each tool directly to see what it returns.

    Think of it as the "first conversation" between a client and a server —
    the handshake that every MCP agent does before it can do anything useful.

What you learn
    Step 1 — CONNECTION  : how a client launches the server as a subprocess (stdio)
    Step 2 — HANDSHAKE   : how the client negotiates capabilities with the server
    Step 3 — LIST TOOLS  : how the client discovers every tool the server exposes
    Step 4 — CALL TOOLS  : how to invoke each tool and inspect the result

    This is the building block for trip_10 (the full MCP agent + Gradio UI).

How to run
    uv run trip_09_mcp_client_demo.py
    (no API key needed — we are NOT calling the LLM yet, only the MCP server)

What you will see
    Connected to MCP server 'trip-buddy'
    4 tools available:
      1. db_lookup          — Look up a destination's full price details...
      2. list_destinations  — List all available trip destinations...
      3. compute_trip_cost  — Compute the exact per-person trip cost...
      4. get_travel_tips    — Retrieve relevant travel tips...

    ── Calling each tool ──
    [db_lookup]          → {'place_id': 'GOA', 'name': 'Goa', ...}
    [list_destinations]  → 5 destinations listed
    [compute_trip_cost]  → {'total_per_person': 11800.0, ...}
    [get_travel_tips]    → - Beach (Goa, Gokarna): best Nov–Feb ...
"""

import asyncio
import json
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient

# ── Server config ─────────────────────────────────────────────────────────────
# We tell the client to launch trip_08_mcp_server.py as a subprocess.
# stdio transport = the client writes to the server's stdin and reads from stdout.
SERVER_CONFIG = {
    "trip-buddy": {
        "command": sys.executable,          # same Python that is running this file
        "args":    ["trip_08_mcp_server.py"],
        "transport": "stdio",
    }
}


async def main() -> None:
    # ── Step 1: CONNECTION ────────────────────────────────────────────────────
    # MultiServerMCPClient is an async context manager.
    # On __aenter__ it launches the server subprocess and opens the stdio pipe.
    print("Connecting to MCP server …")
    async with MultiServerMCPClient(SERVER_CONFIG) as client:

        # ── Step 2: HANDSHAKE ─────────────────────────────────────────────────
        # The MCP handshake happens automatically inside __aenter__.
        # Client sends  →  initialize  (protocol version, capabilities)
        # Server replies →  initialized (its name, capabilities)
        # After this the client knows: "I'm talking to 'trip-buddy'."
        print("✓ Connected. Handshake complete.\n")

        # ── Step 3: LIST TOOLS ────────────────────────────────────────────────
        # get_tools() sends a tools/list request to the server.
        # The server replies with every @mcp.tool() it has registered.
        # We receive them as LangChain BaseTool objects ready to bind to an LLM.
        tools = client.get_tools()

        print(f"{len(tools)} tools available on this server:")
        print("-" * 50)
        for i, t in enumerate(tools, 1):
            # t.name        = the function name
            # t.description = the docstring of the @mcp.tool() function
            first_line = t.description.strip().splitlines()[0]
            print(f"  {i}. {t.name:<22} — {first_line}")
        print()

        # ── Step 4: CALL EACH TOOL ────────────────────────────────────────────
        # ainvoke() sends a tools/call request to the server with the args dict.
        # The server runs the function and sends the result back as JSON.
        # The client returns it as a Python object.

        tool_map = {t.name: t for t in tools}
        sep = "─" * 50

        print(sep)
        print("Calling each tool to verify it works:")
        print(sep)

        # — db_lookup —
        print("\n[1] db_lookup(place='Goa')")
        result = await tool_map["db_lookup"].ainvoke({"place": "Goa"})
        print(json.dumps(result, indent=2))

        # — db_lookup (unknown place) —
        print("\n[2] db_lookup(place='Paris')  ← should return error")
        result = await tool_map["db_lookup"].ainvoke({"place": "Paris"})
        print(json.dumps(result, indent=2))

        # — list_destinations —
        print("\n[3] list_destinations()")
        result = await tool_map["list_destinations"].ainvoke({})
        print(f"  → {len(result)} destinations returned:")
        for d in result:
            print(f"     {d['place_id']:<12} {d['name']:<12} "
                  f"room ₹{d['room_price_per_night']:>5}  "
                  f"travel ₹{d['travel_cost_per_person']:>5}  "
                  f"daily ₹{d['daily_spend_per_person']:>5}")

        # — compute_trip_cost —
        print("\n[4] compute_trip_cost(place='Goa', people=4, nights=3)")
        result = await tool_map["compute_trip_cost"].ainvoke(
            {"place": "Goa", "people": 4, "nights": 3}
        )
        print(json.dumps(result, indent=2))
        print(f"  ✓ Expected total_per_person = 11800.0  "
              f"  Got = {result.get('total_per_person')}")

        # — get_travel_tips —
        print("\n[5] get_travel_tips(query='Manali trip in July')")
        result = await tool_map["get_travel_tips"].ainvoke(
            {"query": "Manali trip in July"}
        )
        print(result)

        print(f"\n{sep}")
        print("All tools called successfully. Server is ready for trip_10 (full agent).")
        print(sep)


if __name__ == "__main__":
    asyncio.run(main())
