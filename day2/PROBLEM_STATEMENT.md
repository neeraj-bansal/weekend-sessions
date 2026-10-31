# Trip Buddy — Problem Statement

## Project Title
**Trip Buddy (DB + RAG + Tools)**

## One-line Description
A conversational group trip-planning assistant that fetches destination prices from a SQLite database, computes exact per-person trip costs with tools, and answers travel advice questions using a RAG knowledge base — served through a Gradio chat UI.

---

## Background

Day 2 of the weekend session teaches six individual building blocks in isolation:

| Lesson | Concept |
|--------|---------|
| `trip_01` | SQLite — structured destination data |
| `trip_02` | Sentence embeddings — cosine similarity |
| `trip_03` | ChromaDB — vector store with metadata |
| `trip_04` | LCEL chain — prompt → LLM → parser |
| `trip_05` | RAG pipeline — retrieve → augment → generate |
| `trip_06` | Tool-calling agent — `@tool`, `bind_tools`, agent loop |

**Trip Buddy** (`trip_07`) is the capstone that wires all six together into a single working product.

---

## Problem Statement

Friend groups struggle to quickly answer:
> *"Can we actually afford this trip — and is now a good time to go?"*

Doing this manually means: looking up hotel prices, splitting room costs, adding travel and daily spend, comparing against a per-person budget, and separately searching for season/safety advice. It is tedious and error-prone.

**Trip Buddy** solves this through a conversational interface where a user types a plain-English question and receives an exact, grounded answer in seconds.

---

## Objective

Build a single Python script (`trip_07_trip_buddy.py`) that:

1. **Stores destination data** in a properly normalised SQLite database (3 tables: `places`, `stays`, `costs`).
2. **Maintains a travel knowledge base** in ChromaDB (season tips, safety warnings, booking advice).
3. **Exposes tools** to a tool-calling LLM agent — written from scratch (not converted from existing `trip_06` functions).
4. **Answers natural-language queries** through a Gradio chat interface.

---

## Target User Queries

These are the **exact 5 example queries** shown as clickable buttons in the Gradio UI (visible in the screenshot). They serve as both the default prompts and the acceptance test cases.

| # | Query (exact text) | Type |
|---|-------------------|------|
| 1 | `list` | List all destinations with prices from DB |
| 2 | `We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?` | Budget feasibility check |
| 3 | `Is Manali a good idea in July?` | Season / safety advice (RAG) |
| 4 | `How much is Hampi for 5 friends, 2 nights?` | Cost estimation |
| 5 | `Which trips fit ₹8,000 each for 3 friends, 2 nights?` | Multi-destination comparison |

> These strings must be passed verbatim as the `examples` list in `gr.ChatInterface(...)`.

---

## Database Design

### The problem with day2's current schema

`trip_01` only created two tables:

```
places  → place_id, name, trip_type
stays   → place_id, stay_name, room_price_per_night
```

`travel_cost_per_person` and `daily_spend_per_person` **do not exist in the DB** — they were hardcoded in a Python dict inside `trip_06`'s `lookup_place`. The agent never talked to the database.

### Corrected 3-table schema for trip_07

```sql
CREATE TABLE places (
    place_id  TEXT PRIMARY KEY,   -- "GOA", "COORG", "MANALI", "HAMPI", "RISHIKESH"
    name      TEXT NOT NULL,
    trip_type TEXT NOT NULL        -- "Beach", "Hills", "Heritage", "Adventure"
);

CREATE TABLE stays (
    place_id             TEXT PRIMARY KEY,
    stay_name            TEXT NOT NULL,
    room_price_per_night INTEGER NOT NULL,
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);

-- NEW: all cost components needed to compute trip cost per person
CREATE TABLE costs (
    place_id               TEXT PRIMARY KEY,
    travel_cost_per_person INTEGER NOT NULL,
    daily_spend_per_person INTEGER NOT NULL,
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);
```

### Seed data

| place_id | Name | Type | Room/night | Stay name | Travel/person | Daily/person |
|----------|------|------|-----------|-----------|--------------|-------------|
| GOA | Goa | Beach | ₹3,000 | Sea Breeze Guesthouse | ₹2,800 | ₹1,500 |
| COORG | Coorg | Hills | ₹2,800 | Coffee Estate Cottage | ₹1,000 | ₹1,100 |
| MANALI | Manali | Hills | ₹2,500 | Boulder Ridge Camp | ₹9,000 | ₹1,300 |
| HAMPI | Hampi | Heritage | ₹1,500 | Boulder View Guesthouse | ₹1,800 | ₹900 |
| RISHIKESH | Rishikesh | Adventure | ₹1,800 | River Camp | ₹2,500 | ₹1,000 |

---

## Tool Design

### Key principle: write tools from scratch, don't convert existing functions

`trip_06` demonstrated converting existing Python functions with `@tool`. In `trip_07` the tools are **written fresh** — each tool body contains its own logic and calls helper functions (e.g. the SQLite cursor, the ChromaDB collection) directly. This teaches the real pattern used in production agents.

### Tool 1 — `db_lookup`
```
db_lookup(place: str) -> dict
```
- Queries SQLite with a 3-table JOIN: `places` + `stays` + `costs`
- Returns: `place_id`, `name`, `trip_type`, `stay_name`, `room_price_per_night`, `travel_cost_per_person`, `daily_spend_per_person`
- Returns `{"error": "..."}` if place not found
- **Replaces** the hardcoded dict in `trip_06`'s `lookup_place`

### Tool 2 — `list_destinations`
```
list_destinations() -> list[dict]
```
- Queries SQLite for all rows (same JOIN as `db_lookup`)
- Returns a list of all destinations — used when user types "list"
- **Replaces** the missing "show me all options" capability from day2

### Tool 3 — `compute_trip_cost`
```
compute_trip_cost(place: str, people: int, nights: int) -> dict
```
- Calls `db_lookup` internally to fetch prices
- Computes in one tool call:
  - `rooms_needed = ceil(people / 2)`
  - `stay_share = rooms_needed × room_price × nights / people`
  - `total_per_person = travel_cost + stay_share + daily_spend × nights`
- Returns the full breakdown: rooms, stay_share, total_per_person
- **Consolidates** `trip_06`'s three-step chain (`lookup_place` → `calculate_stay_share` → `calculate_trip_cost`) into one tool
- All arithmetic is deterministic Python — never left to the LLM

### Tool 4 — `get_travel_tips`
```
get_travel_tips(query: str) -> str
```
- Queries ChromaDB with semantic search (RAG)
- Returns top-2 relevant tips as a bullet string
- **Wires** `trip_05`'s `retrieve_context()` as a proper agent tool for the first time

---

## Functional Requirements

### FR-1 — DB-backed Destination Lookup
`db_lookup` must query the SQLite `costs` table for travel and daily spend — not a hardcoded dict.

### FR-2 — Consolidated Cost Calculation
`compute_trip_cost` must compute rooms, stay share, and total in one deterministic tool. No LLM arithmetic.

### FR-3 — Destination Listing
`list_destinations` must return all places with their price summary from the DB.

### FR-4 — Grounded Travel Advice
`get_travel_tips` must retrieve advice from ChromaDB. Season warnings (e.g. Manali in July) must come from the knowledge base, not LLM training data.

### FR-5 — Budget Feasibility (agent-level reasoning)
The LLM agent compares `compute_trip_cost` output against the user's stated budget and states yes/no with surplus/shortfall. No separate tool needed — this is the LLM's reasoning job once it has the exact numbers.

### FR-6 — Multi-Destination Comparison
The agent calls `list_destinations` then `compute_trip_cost` for each place and ranks them by cost vs budget.

### FR-7 — Gradio Chat UI
Served on `http://localhost:7860` with:
- Chatbot panel
- Text input
- Description line: *"Plan a trip with friends. The agent fetches prices from the DB, does exact maths with tools, and uses the travel notebook for tips. Type **list** to see all destinations."*
- The following 5 strings as pre-filled example buttons (exact text from screenshot):
  ```python
  examples = [
      "list",
      "We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?",
      "Is Manali a good idea in July?",
      "How much is Hampi for 5 friends, 2 nights?",
      "Which trips fit ₹8,000 each for 3 friends, 2 nights?",
  ]
  ```

---

## Non-Functional Requirements

| # | Requirement |
|---|------------|
| NFR-1 | All arithmetic is deterministic Python inside tools — no LLM guessing |
| NFR-2 | Travel advice is grounded in ChromaDB — not LLM training data |
| NFR-3 | Agent loop has `MAX_STEPS ≤ 8` guard |
| NFR-4 | API keys loaded from `.env` via `python-dotenv` — never hardcoded |
| NFR-5 | No new libraries beyond what day2 already uses |

---

## Knowledge Base (ChromaDB)

| ID | Tip | Topic |
|----|-----|-------|
| `beach` | Beach (Goa, Gokarna): best Nov–Feb; shacks close in monsoon. | trip_type |
| `hills` | Hills (Coorg, Manali): best Mar–Jun, Oct. Avoid Jul–Aug: landslides. | trip_type |
| `heritage` | Heritage (Hampi, Jaipur): best Oct–Mar; 40°C+ in Apr–May. | trip_type |
| `adventure` | Adventure (Rishikesh): rafting Oct–Jun, closes in monsoon. | trip_type |
| `buffer` | Keep a 10% buffer for cab surges and missed buses. | travel_tip |
| `book-early` | Book trains/flights 30–60 days early; last-week prices double. | travel_tip |
| `weekdays` | Weekday stays are 20–30% cheaper than weekends. | travel_tip |
| `pack` | Mountain weather changes fast: carry rain jacket and warm layers. | travel_tip |

---

## Implementation Plan

### File to create
`weekend-sessions-main/day2/trip_07_trip_buddy.py`

### Internal sections

```
Section 1 — SQLite setup (3 tables: places, stays, costs)
            ↑ extends trip_01 with the missing costs table

Section 2 — ChromaDB + embeddings
            ↑ same as trip_03 / trip_05

Section 3 — Tool definitions (written from scratch)
              @tool db_lookup(place)           → reads SQLite JOIN
              @tool list_destinations()        → reads all SQLite rows
              @tool compute_trip_cost(place, people, nights)  → calls db_lookup + math
              @tool get_travel_tips(query)     → calls ChromaDB retrieval

Section 4 — Agent loop (from trip_06)
            llm.bind_tools([...]) + TOOL_MAP + run_agent()

Section 5 — Gradio UI
            gr.ChatInterface with example queries
```

### How to run
```bash
cp .env.example .env    # paste OPENAI_API_KEY
uv run trip_07_trip_buddy.py
# → open http://localhost:7860
```

---

## Example Interaction

**User:** We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?

**Agent tool calls:**
```
compute_trip_cost("Goa", 4, 3)
  internally: db_lookup("Goa") → room ₹3000, travel ₹2800, daily ₹1500
  rooms   = ceil(4/2) = 2
  stay    = 2 × 3000 × 3 / 4 = ₹4,500
  total   = 2800 + 4500 + 1500×3 = ₹11,800

get_travel_tips("Goa trip in beach season")
  → "- Beach trips: best Nov–Feb; shacks close in monsoon."
  → "- Book trains 30–60 days early; prices double last week."
```

**Agent final answer:**
> ✅ Yes! Goa for 3 nights costs **₹11,800 per person** — ₹200 under your ₹12,000 budget.
> You'll need 2 rooms. Best time to visit is November to February. Book your trains early!

---

## Success Criteria

- [ ] `db_lookup` reads from SQLite `costs` table — no hardcoded dict
- [ ] `compute_trip_cost` returns exact deterministic numbers (Goa/4/3 → ₹11,800)
- [ ] `list_destinations` returns all 5 places from the DB
- [ ] `get_travel_tips("Manali July")` returns the landslide warning from ChromaDB
- [ ] "Which trips fit ₹8,000?" evaluates all 5 destinations and ranks them
- [ ] Gradio UI launches at `http://localhost:7860` with all 5 example query buttons
