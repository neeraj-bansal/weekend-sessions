# Section 2 — Setup & Run Log

A record of the steps taken to get `day1/section2` (Your First Agent) running on macOS, following [`README.md`](README.md). For the earlier setup (`uv`, Ollama, Groq), see [`../section1/SETUP_LOG.md`](../section1/SETUP_LOG.md).

## 1. Check the starting state

The folder had the scripts and a copied `.env`/`.env.example`, but:

- no `pyproject.toml`, `uv.lock` or `.venv`, so the README's `uv sync` would fail;
- `OPENAI_API_KEY` and `TAVILY_API_KEY` were empty in this folder's `.env`.

Each folder reads its own `.env` (`load_dotenv()` loads the one in the folder you run from), so keys set in Section 1 do not apply here automatically.

## 2. Copy the working `.env` from Section 1

```bash
cd day1/section2
cp ../section1/.env .env
sed -i '' 's|^LANGSMITH_PROJECT=.*|LANGSMITH_PROJECT=section-02-first-agent|' .env
```

The `.env` now holds the Groq settings that work in Section 1:

```
OPENAI_API_KEY=<your Groq key, starts with gsk_>
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-120b
TAVILY_API_KEY=<your Tavily key>
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your LangSmith key>
LANGSMITH_PROJECT=section-02-first-agent
```

- Tavily key (free, 1,000 credits/month): https://app.tavily.com. The name must be exactly `TAVILY_API_KEY`.
- LangSmith tracing is on, so every run appears at https://smith.langchain.com under project `section-02-first-agent`. Set `LANGSMITH_TRACING=false` to turn it off.
- Never commit `.env`.

## 3. Create the project and install dependencies

```bash
cd day1/section2
uv init --bare --no-workspace
uv add python-dotenv langchain langchain-core langchain-openai tavily-python langchain-tavily pydantic
```

This creates `pyproject.toml`, `uv.lock` and `.venv`. Packages match the imports in scripts 01–04:

| Package | Used by |
|---|---|
| `langchain` | `create_agent`, `@tool` (all scripts) |
| `langchain-openai` | `ChatOpenAI` (all scripts) |
| `tavily-python` | `TavilyClient` (script 02) |
| `langchain-tavily` | `TavilySearch` (scripts 03, 04) |
| `pydantic` | `AgentAnswer` model (script 04) |
| `python-dotenv` | `load_dotenv()` (all scripts) |

## 4. Run the scripts

| Script | Command | Result |
|---|---|---|
| 01 | `uv run python 01_agent_with_placeholder_tool.py` | Works |
| 02 | `uv run python 02_agent_with_tavily_sdk_tool.py` | Works |
| 03 | `uv run python 03_agent_with_builtin_tavily_tool.py` | Failed on Groq free tier: `413` token limit (still fails with `max_results=3`) |
| 04 | `uv run python 04_agent_with_structured_output.py` | Not re-run after the change; same cause as 03 |

### Script 01 — placeholder tool

The agent produced 4 messages: question, tool call `search(...)`, the fake tool result (24°C, light drizzle, 78% humidity), final answer. This shows the agent loop without any web access.

### Script 02 — Tavily SDK tool

Two live `search` calls, then a table of three upcoming AI/developer meetups in Bengaluru with dates, venues and links. Each search result was about 13,000 characters of JSON, which the trace printer shortens to one line. Results change from day to day.

### Issue: scripts 03 and 04 — `413 rate_limit_exceeded`

```
openai.APIStatusError: Error code: 413 - Request too large for model `openai/gpt-oss-120b`
... on tokens per minute (TPM): Limit 8000, Requested 11174 ...
```

- Groq's free tier allows 8,000 tokens per minute for `openai/gpt-oss-120b`.
- A single request was over the cap (11,174 tokens at first). Waiting does not help, because the request itself is too big.

**Attempted fix: `TavilySearch(max_results=3)`** in scripts 03 and 04 (with a comment above the line). It did not solve the problem; the next run requested 12,083 tokens.

**What was found while investigating:**

- One Tavily search with `max_results=3` is only about 1.3k tokens, and the tool schema about 1.6k, so neither is the cause.
- The cause is the agent loop. The model keeps calling the search tool (five calls in a row in one trace), and every result stays in the conversation. After three or four searches the request is over 8,000 tokens.
- The model sometimes picks `search_depth: advanced`, which returns longer results.
- Script 02 worked only because the model stopped after two searches. This varies from run to run.
- The rate-limit headers show `openai/gpt-oss-120b`, `openai/gpt-oss-20b` and `qwen/qwen3.8-27b` all have the same 8,000 tokens/min cap, so switching models does not help.

Options:

1. **Upgrade the Groq plan** (Dev Tier) for higher limits: https://console.groq.com/settings/billing. Fixes the cause, but needs a payment method.
2. **Use a provider with higher limits** (a paid OpenAI key works with no code change).
3. **Limit the agent's searches**, for example by asking a narrower question ("Find 1 AI meetup in Bengaluru"). Less like the README, and may still fail on some runs.

The `max_results=3` edits are still in both files; revert them if you prefer the original `TavilySearch()`.

## 5. Format the code (black and isort)

The course lists `black>=25.1` and `isort>=6.0` as optional formatters. There is no `requirements.txt`, so they were added as dev dependencies with `uv`:

```bash
cd day1/section2
uv add --dev "black>=25.1" "isort>=6.0"
uv run black --check . --exclude '\.venv'
uv run isort --check-only --skip .venv .
```

Installed: `black` 26.10.1 and `isort` 9.0.2. `black` first wanted to reformat scripts 03 and 04, because the long trailing comment on the `TavilySearch(max_results=3)` line was too long. The comment was moved onto its own line above the call, and both tools now pass with no changes needed. To format on demand: `uv run black .` and `uv run isort .`.

## 6. Not yet verified

- Scripts 03 and 04 running to completion (need higher token limits).
- Script 04's structured output (`response_format=AgentAnswer`) with Groq.

## Quick reference

| Problem | Fix |
|---|---|
| `MissingAPIKeyError` / Tavily 401 | `TAVILY_API_KEY` missing or misspelled in this folder's `.env` |
| `OPENAI_API_KEY` empty | Copy `../section1/.env` or paste the key; each folder has its own `.env` |
| `413 rate_limit_exceeded` on Groq | The agent's repeated searches grow the request past 8k tokens/min. `max_results` and smaller models do not fix it; upgrade the plan or use another provider |
| `429` on Groq | Free-tier rate limit; wait a minute and re-run |
| `ModuleNotFoundError` | Run with `uv run`, not system `python3` |
| Runs show up in LangSmith unexpectedly | Set `LANGSMITH_TRACING=false` in `.env` |
