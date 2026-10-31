# Trip Buddy MCP — Solution Design

> This document is the technical companion to `MCP_PROBLEM_STATEMENT.md`.
> It covers architecture decisions, wire mechanics, code skeletons, and how to run everything.

---

## Architecture

```
nb_trip_09_mcp_client_demo.py  OR  nb_trip_10_mcp_agent.py
        │
        │  subprocess.Popen  (stdio transport)
        ▼
nb_trip_08_mcp_server.py
┌───────────────────────────────────────┐
│  SQLite DB          ChromaDB KB       │
│  (places/stays/costs)  (8 tips)       │
│                                       │
│  @mcp.tool() db_lookup                │
│  @mcp.tool() list_destinations        │
│  @mcp.tool() compute_trip_cost        │
│  @mcp.tool() get_travel_tips          │
└───────────────────────────────────────┘
        │  JSON-RPC 2.0 over stdin/stdout
        ▼
LLM (OpenAI) with discovered tools bound
        │
        ▼
Gradio ChatInterface  →  http://localhost:7860
```

---

## Transport: stdio (local)

| Transport | How it works | When to use |
|-----------|-------------|-------------|
| **stdio** | Client spawns server as subprocess; JSON-RPC over stdin/stdout pipes | Same machine — no network needed |
| SSE/HTTP | Client connects to a URL | Remote server on cloud/container |

Trip Buddy uses **stdio**. The client launches `nb_trip_08_mcp_server.py` via `subprocess.Popen` using the same Python interpreter (`sys.executable`). All JSON-RPC 2.0 messages are framed with `Content-Length` headers — the MCP SDK handles this automatically; you never write the wire format by hand.

### Message sequence
```
Client                              Server
──────                              ──────
subprocess.Popen(server) ─────────▶ starts, loads DB + KB
send: initialize ─────────────────▶
                          ◀──────── initialized
send: tools/list ─────────────────▶
                          ◀──────── [db_lookup, list_destinations,
                                     compute_trip_cost, get_travel_tips]
send: tools/call ─────────────────▶
                          ◀──────── result JSON
...
context manager exits ────────────▶ subprocess terminated
```

---

## New Dependencies

```toml
# add to pyproject.toml / uv.lock
mcp[cli]
langchain-mcp-adapters
```

---

## nb_trip_08_mcp_server.py — Solution

### Structure
```
Section 1 — SQLite setup   (3 tables: places, stays, costs — same as trip_07)
Section 2 — ChromaDB setup (8 tips — same as trip_07)
Section 3 — FastMCP tool registrations (@mcp.tool())
Section 4 — mcp.run()      (starts stdio server, blocks until client disconnects)
```

### Key difference from trip_07
`trip_07` uses LangChain's `@tool`. `trip_08` uses FastMCP's `@mcp.tool()`. The tool body (SQL, math, ChromaDB queries) is **identical**. Only the decorator and import change.

| trip_07 | trip_08 |
|---------|---------|
| `from langchain_core.tools import tool` | `from mcp.server.fastmcp import FastMCP` |
| `@tool` | `@mcp.tool()` |
| `llm.bind_tools(tools)` (in agent) | `mcp.run()` (serves tools to any client) |

### Tool signatures
```python
mcp = FastMCP("trip-buddy")

@mcp.tool()
def db_lookup(place: str) -> dict:
    """Look up a destination's full price details from the database.
    Returns place_id, name, trip_type, stay_name, room_price_per_night,
    travel_cost_per_person, daily_spend_per_person.
    Returns {"error": "..."} if destination not found."""

@mcp.tool()
def list_destinations() -> list[dict]:
    """List all available trip destinations with their prices.
    Returns a list of dicts (same fields as db_lookup)."""

@mcp.tool()
def compute_trip_cost(place: str, people: int, nights: int) -> dict:
    """Compute the exact per-person trip cost.
    rooms_needed = ceil(people / 2)
    stay_share   = rooms * room_price * nights / people
    total        = travel_cost + stay_share + daily_spend * nights
    Returns full breakdown plus total_per_person."""

@mcp.tool()
def get_travel_tips(query: str) -> str:
    """Retrieve the 2 most relevant travel tips using semantic search."""

if __name__ == "__main__":
    mcp.run()   # stdio transport — blocks, reads from stdin
```

---

## nb_trip_09_mcp_client_demo.py — Solution

**Purpose:** Verify the server works end-to-end before wiring the LLM. No OpenAI key needed.

### Structure
```
Step 1 — CONNECTION : MultiServerMCPClient(SERVER_CONFIG) as async context manager
Step 2 — HANDSHAKE  : automatic in __aenter__ (initialize / initialized)
Step 3 — LIST TOOLS : client.get_tools() → prints name + description for each
Step 4 — CALL TOOLS : ainvoke() each tool with test inputs → prints results
```

### Server config (stdio)
```python
import sys

SERVER_CONFIG = {
    "trip-buddy": {
        "command":   sys.executable,             # same Python that runs this file
        "args":      ["nb_trip_08_mcp_server.py"],  # server script path
        "transport": "stdio",                    # local — no URL
    }
}
```

### Connection and tool listing
```python
async with MultiServerMCPClient(SERVER_CONFIG) as client:
    # Handshake complete at this point
    tools = client.get_tools()   # sends tools/list to server
    for t in tools:
        print(f"{t.name}: {t.description.splitlines()[0]}")
```

### Calling each tool
```python
tool_map = {t.name: t for t in tools}

# db_lookup
result = await tool_map["db_lookup"].ainvoke({"place": "Goa"})

# list_destinations
result = await tool_map["list_destinations"].ainvoke({})

# compute_trip_cost — expected: total_per_person = 11800.0
result = await tool_map["compute_trip_cost"].ainvoke(
    {"place": "Goa", "people": 4, "nights": 3}
)

# get_travel_tips
result = await tool_map["get_travel_tips"].ainvoke(
    {"query": "Manali trip in July"}
)
```

### How to run
```bash
uv run nb_trip_09_mcp_client_demo.py
# no OPENAI_API_KEY needed
```

---

## nb_trip_10_mcp_agent.py — Solution

**Purpose:** Full MCP client agent with LLM loop + Gradio UI.

### Structure
```
Section 1 — SERVER_CONFIG (stdio, same as trip_09)
Section 2 — run_agent(query) — async agent loop using MCP tools
Section 3 — Gradio ChatInterface with 5 example queries
```

### Agent loop
```python
async def run_agent(query: str) -> str:
    async with MultiServerMCPClient(SERVER_CONFIG) as client:
        tools    = client.get_tools()           # tools/list from server
        TOOL_MAP = {t.name: t for t in tools}

        llm = ChatOpenAI(model=MODEL, reasoning_effort="none").bind_tools(tools)

        messages = [HumanMessage(content=query)]
        for _ in range(MAX_STEPS):
            response = llm.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return response.text

            for tc in response.tool_calls:
                result = await TOOL_MAP[tc["name"]].ainvoke(tc["args"])  # tools/call
                messages.append(ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tc["id"],
                ))

    return "No answer."
```

### Gradio UI (identical to trip_07)
```python
import gradio as gr

EXAMPLES = [
    "list",
    "We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?",
    "Is Manali a good idea in July?",
    "How much is Hampi for 5 friends, 2 nights?",
    "Which trips fit ₹8,000 each for 3 friends, 2 nights?",
]

def chat(message, history):
    return asyncio.run(run_agent(message))

demo = gr.ChatInterface(
    fn=chat,
    title="Trip Buddy (DB + RAG + Tools)",
    description=(
        "Plan a trip with friends. The agent fetches prices from the DB, "
        "does exact maths with tools, and uses the travel notebook for tips. "
        "Type **list** to see all destinations."
    ),
    examples=EXAMPLES,
)

if __name__ == "__main__":
    demo.launch()
```

### How to run
```bash
cp .env.example .env    # paste OPENAI_API_KEY
uv run nb_trip_10_mcp_agent.py
# → open http://localhost:7860
```

> **Do NOT run trip_08 manually.** `MultiServerMCPClient` spawns it automatically as a subprocess.
> Running it in a terminal would block waiting on stdin with no output.

---

## trip_07 vs MCP — Side-by-side Comparison

| Aspect | trip_07 | trip_08 + trip_09/10 |
|--------|---------|----------------------|
| Tool registration | `@tool` (LangChain) | `@mcp.tool()` (FastMCP) |
| Tool discovery | Hardcoded `TOOL_MAP` | `client.get_tools()` at runtime |
| DB / RAG location | Same process as agent | Server process only |
| Agent imports | sqlite3, chromadb, sentence_transformers | None of these |
| Reusability | Single agent | Any MCP-compatible host |
| Process count | 1 | 2 (server + client) |
| Transport | None (in-process calls) | stdio (subprocess pipes) |

---

## Example Interaction

**User:** Which trips fit ₹8,000 each for 3 friends, 2 nights?

**Agent tool calls (over MCP stdio):**
```
list_destinations()
  → [GOA, COORG, MANALI, HAMPI, RISHIKESH]

compute_trip_cost("GOA", 3, 2)        → total_per_person: 10266.67
compute_trip_cost("COORG", 3, 2)      → total_per_person: 5466.67
compute_trip_cost("HAMPI", 3, 2)      → total_per_person: 5300.0
compute_trip_cost("RISHIKESH", 3, 2)  → total_per_person: 6100.0
compute_trip_cost("MANALI", 3, 2)     → total_per_person: 14333.33

get_travel_tips("budget trip India")
  → "- Weekday stays are 20–30% cheaper than weekends."
     "- Book trains 30–60 days early; prices double last week."
```

**Agent final answer:**
> 3 of 5 destinations fit ₹8,000/person for 2 nights:
> 1. **Hampi** — ₹5,300 ✅
> 2. **Coorg** — ₹5,467 ✅
> 3. **Rishikesh** — ₹6,100 ✅
>
> Goa (₹10,267) and Manali (₹14,333) are over budget. Travelling on weekdays can save 20–30% on stays!
