# Trip Buddy — Problem Statement

## Project Title
**Trip Buddy (DB + RAG + Tools)**

## One-line Description
A conversational group trip-planning assistant that fetches destination prices from a database, does exact cost arithmetic with tools, and answers travel advice questions using a RAG knowledge base — served through a Gradio chat UI.

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

**Trip Buddy** is the capstone that wires all six together into a single, working product.

---

## Problem Statement

Friend groups struggle to quickly answer the question:  
> *"Can we actually afford this trip — and is now a good time to go?"*

Doing this manually means: looking up hotel prices, splitting room costs, adding travel and daily spend, comparing against a per-person budget, and separately searching for season/safety advice. It is tedious and error-prone.

**Trip Buddy** solves this through a conversational interface where a user can type a plain-English question and receive an exact, grounded answer in seconds.

---

## Objective

Build a single Python script (`trip_07_trip_buddy.py`) that:

1. **Stores destination data** in SQLite (places, stay prices, travel costs, daily spend).
2. **Maintains a travel knowledge base** in ChromaDB (season tips, safety warnings, booking advice) with sentence embeddings.
3. **Exposes five tools** to a tool-calling LLM agent for deterministic computation and grounded retrieval.
4. **Answers natural-language queries** through a Gradio chat interface.

---

## Target User Queries

The assistant must handle all of the following:

| Query | Type |
|-------|------|
| `list` | List all available destinations with prices |
| `We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?` | Budget feasibility check |
| `Is Manali a good idea in July?` | Season / safety advice (RAG) |
| `How much is Hampi for 5 friends, 2 nights?` | Cost estimation |
| `Which trips fit ₹8,000 each for 3 friends, 2 nights?` | Multi-destination comparison |

---

## Functional Requirements

### FR-1 — Destination Lookup
The agent must retrieve prices (room rate, travel cost, daily spend, trip type) for any stored destination by name (case-insensitive).

### FR-2 — Exact Cost Calculation
The agent must compute:
- **Rooms needed** = `ceil(people / 2)` (one room fits 2 people)
- **Stay share** = `rooms × room_price × nights / people`
- **Total per person** = `travel_cost + stay_share + daily_spend × nights`

All arithmetic must be done by a deterministic Python tool — never left to the LLM.

### FR-3 — Budget Feasibility Verdict
Given a per-person budget and the computed cost, the agent must return:
- A clear **yes/no** verdict
- The **surplus** (budget left over) or **shortfall** (how much more is needed) per person

### FR-4 — Season & Travel Advice
The agent must retrieve relevant travel tips from the ChromaDB knowledge base using semantic search (RAG). Topics covered: best months, monsoon warnings, booking tips, packing advice.

### FR-5 — Multi-Destination Comparison
When asked "which trips fit my budget?", the agent must evaluate all destinations and return a ranked list of feasible options with cost per person.

### FR-6 — Gradio Chat UI
The assistant must be served through a **Gradio Chatbot** interface with:
- A text input box
- Pre-filled example queries as clickable buttons (as shown in the UI screenshot)
- A short description: *"Plan a trip with friends. The agent fetches prices from the DB, does exact maths with tools, and uses the travel notebook for tips."*

---

## Non-Functional Requirements

| # | Requirement |
|---|------------|
| NFR-1 | All arithmetic results must be **deterministic** (no LLM guessing) |
| NFR-2 | Travel advice must be **grounded** in the knowledge base, not LLM training data |
| NFR-3 | The agent loop must have a **MAX_STEPS** guard (≤ 8) to prevent infinite loops |
| NFR-4 | No hardcoded API keys — load from `.env` via `python-dotenv` |
| NFR-5 | No new libraries beyond what day2 already uses |

---

## Tools to Implement

| Tool | Status | Description |
|------|--------|-------------|
| `lookup_place(place)` | Reuse from `trip_06` | Fetch destination prices from SQLite |
| `calculate_stay_share(room_price, nights, people)` | Reuse from `trip_06` | Exact room-split arithmetic |
| `calculate_trip_cost(travel, stay_share, daily, nights)` | Reuse from `trip_06` | Total per-person cost |
| `check_budget(budget, cost)` | **New** | Yes/no verdict + surplus/shortfall |
| `get_season_advice(place, month)` | **New** | ChromaDB RAG retrieval as a tool |
| `list_destinations()` | **New** | Return all places with prices (for "list" query) |
| `find_affordable_destinations(budget, people, nights)` | **New** | Multi-destination comparison |

---

## Destination Data (Seed)

| Place | Type | Room/night | Travel/person | Daily/person |
|-------|------|-----------|--------------|-------------|
| Goa | Beach | ₹3,000 | ₹2,800 | ₹1,500 |
| Coorg | Hills | ₹2,800 | ₹1,000 | ₹1,100 |
| Manali | Hills | ₹2,500 | ₹9,000 | ₹1,300 |
| Hampi | Heritage | ₹1,500 | ₹1,800 | ₹900 |
| Rishikesh | Adventure | ₹1,800 | ₹2,500 | ₹1,000 |

---

## Knowledge Base (ChromaDB Tips)

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
Section 1 — SQLite setup        (trip_01 pattern)
Section 2 — ChromaDB + embeddings (trip_03 + trip_05 pattern)
Section 3 — Tool definitions    (trip_06 pattern + 3 new tools)
Section 4 — Agent loop          (trip_06 pattern)
Section 5 — Gradio UI           (new)
```

### How to run
```bash
# 1. Set your OpenAI key
cp .env.example .env   # paste OPENAI_API_KEY

# 2. Run
uv run trip_07_trip_buddy.py

# 3. Open browser at http://localhost:7860
```

---

## Example Interaction

**User:** We are 4 friends with ₹12,000 each. Can we do Goa for 3 nights?

**Agent (tool calls):**
```
lookup_place("Goa")               → room ₹3000, travel ₹2800, daily ₹1500
calculate_stay_share(3000, 3, 4)  → rooms=2, stay_share=₹4500
calculate_trip_cost(2800, 4500, 1500, 3) → ₹11,800
check_budget(12000, 11800)        → feasible=True, surplus=₹200
get_season_advice("Goa", "")      → "Beach trips: best Nov–Feb..."
```

**Agent (final answer):**  
> ✅ Yes! Goa for 3 nights costs **₹11,800 per person** — ₹200 under your ₹12,000 budget.  
> You'll need 2 rooms. Best time to visit is November–February when beaches and water sports are fully open. Book your trains at least 30 days early.

---

## Success Criteria

- [ ] All 5 example queries from the UI return correct, grounded answers
- [ ] Budget arithmetic is exact (no LLM rounding errors)
- [ ] Season advice for Manali in July warns about landslides (RAG-sourced)
- [ ] "Which trips fit ₹8,000?" returns a ranked list of feasible destinations
- [ ] Gradio UI launches at `http://localhost:7860` with example query buttons
