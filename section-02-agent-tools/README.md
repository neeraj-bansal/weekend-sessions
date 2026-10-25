# Section 2 — Giving Agents Tools

Two complementary tracks — Strands notebooks and LangChain scripts — both covering the same concept: turning Python functions into tools an LLM can call.

---

## Notebooks (Strands Agents)

| Notebook | What it covers |
|---|---|
| `01_building_tools.ipynb` | Function → tool with `@tool`, a tip calculator, a multi-tool sales assistant, a custom inventory checker |
| `02_prebuilt_and_aws_tools.ipynb` | Prebuilt tools (`calculator`, `http_request`, `file_write`) and `use_aws` against S3, DynamoDB and Lambda |
| `03_advanced_tool_patterns.ipynb` | The database-connection problem and class-based tools; async tools that run in parallel |

## Scripts (LangChain + LangGraph)

| File | What it shows | Needs |
|---|---|---|
| `01_agent_with_placeholder_tool.py` | Agent loop with a fake `search` tool (always returns Bengaluru weather) | `OPENAI_API_KEY` |
| `02_agent_with_tavily_sdk_tool.py` | Your own `search` tool wrapping the Tavily SDK (real web search) | + `TAVILY_API_KEY` |
| `03_agent_with_builtin_tavily_tool.py` | The vendor's ready-made `TavilySearch` tool | + `TAVILY_API_KEY` |
| `04_agent_with_structured_output.py` | `response_format=AgentAnswer` → validated Pydantic object with titled sources | + `TAVILY_API_KEY` |
| `agent_trace_printer.py` | Helper that prints agent messages one per line | — |

Each script changes **one thing** vs the previous one — open two files side by side to see the diff.

---

## Setup

### Notebooks — Bedrock (default)

```bash
pip install -r requirements.txt
jupyter lab
```

### Notebooks — Groq (no AWS needed)

```bash
pip install -r requirements-groq.txt
jupyter lab
```

### Scripts — uv

```bash
uv sync          # installs pyproject.toml deps (LangChain + Tavily)
cp .env.example .env   # or symlink: ln -s <root>/.env .env
```

Get a free Tavily key (1 000 credits/month) at https://app.tavily.com.

---

## Run

```bash
# Notebooks
jupyter lab 01_building_tools.ipynb

# Scripts
uv run python 01_agent_with_placeholder_tool.py
uv run python 02_agent_with_tavily_sdk_tool.py
uv run python 02_agent_with_tavily_sdk_tool.py "What's the weather in Bengaluru right now?"
uv run python 03_agent_with_builtin_tavily_tool.py
uv run python 04_agent_with_structured_output.py
```

---

## How the agent loop works

```
question ──► LLM ──"call search('...')"──► LangChain runs search()
               ▲                                       │
               └──── ToolMessage("result ...") ────────┘
LLM ──► final answer (no more tool calls → done)
```

- The LLM **never runs code** — it only *requests* a tool call; LangChain executes it.
- `@tool` sends the function's **name, type hints and docstring** to the model.
- `response_format=AgentAnswer` uses either **ProviderStrategy** (native structured output) or **ToolStrategy** (an "answer" tool) depending on the model.

---

## Note on deprecation warnings

`strands-agents-tools` 0.8.x prints a deprecation notice for some prebuilt tools (`calculator`, `http_request`, `tavily`, `current_time`). They still work — this course pins `strands-agents-tools<0.9`. Replacements: `http_request`/`web_fetch` from `strands.vended_tools`, the official Tavily MCP server, and `ContextInjector` for current time.

---

## Optional: LangSmith tracing

Add to `.env`:
```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=section-02-agent-tools
```

Each script run shows the full agent loop in LangSmith: tool call → tool result → final answer.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `MissingAPIKeyError` / Tavily 401 | `TAVILY_API_KEY` missing or misspelled in `.env` |
| Agent answers without searching | Make the docstring more explicit, or ask something needing fresh data |
| `result["structured_response"]` KeyError | Only script 04 sets `response_format` — use that one |

---

**Previous:** [Section 1 — Your First Agent](../section-01-your-first-agent/README.md) · **Next:** [Section 3 — Agent Memory](../../day1/section-03-agent-memory/README.md)
