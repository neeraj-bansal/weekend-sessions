"""
trip_08_mcp_server.py
─────────────────────
Lesson 08 · MCP Server: expose Trip Buddy's tools over the Model Context Protocol.

The story
    trip_07 wired the DB, RAG, tools, and agent all in one file. Now we split
    responsibilities. This file is the SERVER — it owns the data and the tools.
    Any MCP-compatible client (our agent, Claude Desktop, another LLM) can connect
    to it without knowing anything about SQLite or ChromaDB.

What you learn
    - FastMCP turns plain Python functions into MCP tools with @mcp.tool()
    - The server owns the DB + knowledge base; clients just call tools
    - stdio transport = the client launches this script as a subprocess

How to run (standalone test)
    uv run trip_08_mcp_server.py
    (normally launched as a subprocess by trip_09 — not run directly)
"""

import math
import sqlite3

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from mcp.server.fastmcp import FastMCP

# ── 1. SQLite setup (3 tables: places + stays + costs) ───────────────────────
# Extends trip_01's schema with the missing `costs` table so the agent
# never needs to read from a hardcoded dict again.

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript("""
CREATE TABLE places (
    place_id  TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    trip_type TEXT NOT NULL
);
CREATE TABLE stays (
    place_id             TEXT PRIMARY KEY,
    stay_name            TEXT NOT NULL,
    room_price_per_night INTEGER NOT NULL,
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);
CREATE TABLE costs (
    place_id               TEXT PRIMARY KEY,
    travel_cost_per_person INTEGER NOT NULL,
    daily_spend_per_person INTEGER NOT NULL,
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);
""")

cur.executemany("INSERT INTO places VALUES (?,?,?)", [
    ("GOA",       "Goa",       "Beach"),
    ("COORG",     "Coorg",     "Hills"),
    ("MANALI",    "Manali",    "Hills"),
    ("HAMPI",     "Hampi",     "Heritage"),
    ("RISHIKESH", "Rishikesh", "Adventure"),
])
cur.executemany("INSERT INTO stays VALUES (?,?,?)", [
    ("GOA",       "Sea Breeze Guesthouse",   3000),
    ("COORG",     "Coffee Estate Cottage",   2800),
    ("MANALI",    "Boulder Ridge Camp",      2500),
    ("HAMPI",     "Boulder View Guesthouse", 1500),
    ("RISHIKESH", "River Camp",              1800),
])
cur.executemany("INSERT INTO costs VALUES (?,?,?)", [
    ("GOA",       2800, 1500),
    ("COORG",     1000, 1100),
    ("MANALI",    9000, 1300),
    ("HAMPI",     1800,  900),
    ("RISHIKESH", 2500, 1000),
])
conn.commit()

# ── 2. ChromaDB knowledge base (trip_03 / trip_05 pattern) ───────────────────
embed = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

chroma = chromadb.Client()
col = chroma.create_collection("trip_tips", metadata={"hnsw:space": "cosine"})

TIPS = [
    ("beach",      "Beach (Goa, Gokarna): best Nov–Feb; shacks close in monsoon.",              {"topic": "trip_type"}),
    ("hills",      "Hills (Coorg, Manali): best Mar–Jun and Oct. Avoid Jul–Aug: landslides.",   {"topic": "trip_type"}),
    ("heritage",   "Heritage (Hampi, Jaipur): best Oct–Mar; 40°C+ afternoons in Apr–May.",      {"topic": "trip_type"}),
    ("adventure",  "Adventure (Rishikesh): rafting runs Oct–Jun and closes in the monsoon.",    {"topic": "trip_type"}),
    ("buffer",     "Keep a 10% buffer on top of the total for cab surges and missed buses.",    {"topic": "travel_tip"}),
    ("book-early", "Book trains and flights 30–60 days early; prices often double last week.",  {"topic": "travel_tip"}),
    ("weekdays",   "Weekday stays are 20–30% cheaper than weekends.",                           {"topic": "travel_tip"}),
    ("pack",       "Mountain weather changes fast: carry a rain jacket and warm layers.",        {"topic": "travel_tip"}),
]
vecs = embed.embed_documents([text for _, text, _ in TIPS])
col.add(
    ids=[tid for tid, _, _ in TIPS],
    embeddings=vecs,
    documents=[text for _, text, _ in TIPS],
    metadatas=[meta for _, _, meta in TIPS],
)

# ── 3. MCP server ─────────────────────────────────────────────────────────────
mcp = FastMCP("trip-buddy")


@mcp.tool()
def db_lookup(place: str) -> dict:
    """
    Look up a destination's full price details from the database.
    Returns place_id, name, trip_type, stay_name, room_price_per_night,
    travel_cost_per_person, and daily_spend_per_person.
    Returns {"error": "..."} if the destination is not found.
    """
    row = cur.execute(
        """
        SELECT p.place_id, p.name, p.trip_type,
               s.stay_name, s.room_price_per_night,
               c.travel_cost_per_person, c.daily_spend_per_person
        FROM   places p
        JOIN   stays  s ON s.place_id = p.place_id
        JOIN   costs  c ON c.place_id = p.place_id
        WHERE  UPPER(p.place_id) = UPPER(?)
        """,
        (place,),
    ).fetchone()
    return dict(row) if row else {"error": f"'{place}' not found in the database."}


@mcp.tool()
def list_destinations() -> list[dict]:
    """
    List all available trip destinations with their prices.
    Returns a list of dicts, each with place_id, name, trip_type,
    stay_name, room_price_per_night, travel_cost_per_person, daily_spend_per_person.
    """
    rows = cur.execute(
        """
        SELECT p.place_id, p.name, p.trip_type,
               s.stay_name, s.room_price_per_night,
               c.travel_cost_per_person, c.daily_spend_per_person
        FROM   places p
        JOIN   stays  s ON s.place_id = p.place_id
        JOIN   costs  c ON c.place_id = p.place_id
        ORDER  BY p.name
        """
    ).fetchall()
    return [dict(r) for r in rows]


@mcp.tool()
def compute_trip_cost(place: str, people: int, nights: int) -> dict:
    """
    Compute the exact per-person trip cost for a destination.
    Fetches prices from the DB, then calculates:
      rooms_needed     = ceil(people / 2)   (one room fits 2 people)
      stay_share       = rooms * room_price * nights / people
      total_per_person = travel_cost + stay_share + daily_spend * nights
    Returns the full breakdown plus total_per_person.
    """
    info = db_lookup(place)
    if "error" in info:
        return info
    rooms   = math.ceil(people / 2)
    stay    = round(rooms * info["room_price_per_night"] * nights / people, 2)
    total   = round(info["travel_cost_per_person"] + stay + info["daily_spend_per_person"] * nights, 2)
    return {
        "place":             info["name"],
        "trip_type":         info["trip_type"],
        "people":            people,
        "nights":            nights,
        "rooms_needed":      rooms,
        "stay_share":        stay,
        "travel_cost":       info["travel_cost_per_person"],
        "daily_spend":       info["daily_spend_per_person"],
        "total_per_person":  total,
    }


@mcp.tool()
def get_travel_tips(query: str) -> str:
    """
    Retrieve relevant travel tips from the knowledge base using semantic search.
    Returns the top 2 matching tips as a bullet-point string.
    """
    qv  = embed.embed_query(query)
    res = col.query(query_embeddings=[qv], n_results=2)
    tips = res["documents"][0]
    return "\n".join(f"- {t}" for t in tips) if tips else "No specific tips found."


# ── 4. Start server ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()   # default: stdio transport
