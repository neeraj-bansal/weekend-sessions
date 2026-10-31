# Trip Buddy MCP — Problem Statement

## Project Title
**Trip Buddy MCP (Model Context Protocol Extension)**

## One-line Description
Extend Trip Buddy so its tools are exposed as a local MCP server and consumed by a separate MCP client agent — decoupling data/tool ownership from the LLM agent.

---

## Background

`trip_07_trip_buddy.py` works but has one architectural weakness: the database, the knowledge base, the tools, and the LLM agent all live in one file. If you want a different LLM, a different UI, or a second agent to use the same tools, you have to copy and re-implement everything.

**Model Context Protocol (MCP)** solves this by standardising how agents discover and call tools hosted in a separate process. With MCP, the tools become a standalone service. Any compatible host — another agent, Claude Desktop, a future trip comparison bot — can connect and use them without knowing anything about SQLite or ChromaDB.

---

## Problem Statement

> *The tools built in trip_07 are locked inside a single script. They cannot be reused by other agents or hosts without duplicating code. There is no separation between "what the tools do" and "who calls them".*

Trip Buddy MCP solves this by splitting the system into two independent roles:

| Role | Responsibility |
|------|----------------|
| **MCP Server** | Owns the data (SQLite DB + ChromaDB KB) and exposes tools |
| **MCP Client / Agent** | Connects to the server, discovers tools at runtime, drives the LLM |

---

## Objectives

1. Build a **local MCP server** (`trip_08`) that owns the Trip Buddy data and exposes all tools over stdio transport.
2. Build a **MCP client demo** (`trip_09`) that connects to the server, performs the handshake, lists all available tools, and calls each one to verify they work — without involving the LLM.
3. Build a **MCP client agent** (`trip_10`) that uses the MCP-discovered tools to drive the full LLM agent loop and serve the same Gradio chat UI as `trip_07`.

---

## Target User Queries (same as trip_07)

The MCP agent must answer all 5 queries identically to `trip_07`:

| # | Query | Type |
|---|-------|------|
| 1 | `list` | List all destinations with prices |
| 2 | `We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?` | Budget feasibility |
| 3 | `Is Manali a good idea in July?` | Season / safety advice |
| 4 | `How much is Hampi for 5 friends, 2 nights?` | Cost estimation |
| 5 | `Which trips fit ₹8,000 each for 3 friends, 2 nights?` | Multi-destination comparison |

---

## Functional Requirements

### FR-MCP-1 — MCP Server exposes all Trip Buddy tools
The server must register the same 4 tools from `trip_07` (`db_lookup`, `list_destinations`, `compute_trip_cost`, `get_travel_tips`) so they are callable by any MCP-compatible client.

### FR-MCP-2 — Server owns all data
The server is the sole owner of the SQLite database and the ChromaDB knowledge base. No client should need to import or initialise either.

### FR-MCP-3 — Client discovers tools at runtime
The client must not hardcode tool names, signatures, or schemas. It must retrieve the tool list from the server at connection time.

### FR-MCP-4 — Client demo verifies the connection end-to-end
Before building the full agent, a standalone demo script must:
- Connect to the server and complete the handshake
- Print all discovered tools with their descriptions
- Call each tool once with representative inputs and print the results

### FR-MCP-5 — Client agent answers all 5 target queries
The full MCP client agent must produce the same answers as `trip_07` for all 5 example queries.

### FR-MCP-6 — Client agent serves a Gradio chat UI
The Gradio UI must be identical to `trip_07`: same description text, same 5 example query buttons.

### FR-MCP-7 — Client has zero knowledge of data internals
The client agent must not import `sqlite3`, `chromadb`, or `sentence_transformers`. All data access must flow through the MCP server.

---

## Non-Functional Requirements

| # | Requirement |
|---|------------|
| NFR-MCP-1 | Server and client run as **separate processes** on the same machine |
| NFR-MCP-2 | Transport is **stdio** (local) — no HTTP server, no network port, no URL |
| NFR-MCP-3 | The client spawns the server automatically — users run only one command |
| NFR-MCP-4 | All tool results must be deterministic (same guarantee as `trip_07`) |
| NFR-MCP-5 | API keys loaded from `.env` — never hardcoded |
| NFR-MCP-6 | No new libraries introduced beyond `mcp[cli]` and `langchain-mcp-adapters` |

---

## Files to Produce

| File | Purpose |
|------|---------|
| `trip_08_mcp_server.py` | MCP server — data + tools |
| `trip_09_mcp_client_demo.py` | Connection / handshake / tool listing demo (no LLM) |
| `trip_10_mcp_agent.py` | Full MCP client agent + Gradio UI |

---

## Success Criteria

- [ ] `trip_08` starts and exposes exactly 4 tools with correct schemas
- [ ] `trip_09` connects, lists all 4 tools, and calls each one successfully without an LLM
- [ ] `compute_trip_cost("Goa", 4, 3)` returns `total_per_person = 11800.0` via the MCP call
- [ ] `get_travel_tips("Manali July")` returns the landslide warning from ChromaDB via the MCP call
- [ ] `trip_10` answers all 5 example queries correctly through the MCP server
- [ ] `trip_10` imports no data libraries (`sqlite3`, `chromadb`, `sentence_transformers`)
- [ ] Gradio UI launches at `http://localhost:7860` with all 5 example query buttons
