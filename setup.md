# Setup & Run Log

Combined setup notes for Sections 1–3, kept in section order. Each section keeps its original headings, one level down.

> **Paths.** Commands use the current repo layout (`section-01-your-first-agent/`, `section-02-agent-tools/`, `section-03-agent-memory/` at the repo root). The logs were first written when the sections lived under `day1/`; Section 3's merge steps keep the old `day1/…` paths on purpose, as history.
> **`.env`.** Start from the root `.env.template` (`cp .env.template .env`). In this workspace each section's `.env` is a symlink to one shared `.env`, so a key set once applies everywhere; the Section 1–2 notes about separate per-folder `.env` files describe the original setup.

- [Section 1 — Setup & Run Log](#section-1--setup--run-log) — `section-01-your-first-agent/`
- [Section 2 — Setup & Run Log](#section-2--setup--run-log) — `section-02-agent-tools/`
- [Section 3 — Setup & Run Log](#section-3--setup--run-log) — `section-03-agent-memory/`

---

## Section 1 — Setup & Run Log

A record of the steps taken to get `section-01-your-first-agent` working on macOS (Apple Silicon), following [`section-01-your-first-agent/README.md`](section-01-your-first-agent/README.md).

### 1. Create the `.env` file

The README says `cp .env.example .env`, but the repo has no `.env.example`. Copy the root `.env.template` instead (it lists the same variables).

Starter `.env` contents (keys left empty):

```
OPENAI_API_KEY=

# Use Groq (free tier) through the OpenAI-compatible API.
# For real OpenAI, remove OPENAI_BASE_URL and set OPENAI_MODEL=gpt-5.6-sol.
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-120b

OLLAMA_MODEL=gemma3:270m

# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=lsv2_...
# LANGSMITH_PROJECT=section-01-langchain-foundations

# Required for section-02-agent-tools scripts 02-04 (free key: https://app.tavily.com)
TAVILY_API_KEY=
```

```bash
cd section-01-your-first-agent
cp ../.env.template .env
```

Then paste your real `OPENAI_API_KEY` into `.env`.

> Never commit `.env`. Add it to `.gitignore` if the folder is ever put under git.

### 2. Add the Tavily key (needed by Section 2)

Section 2 scripts 02–04 call Tavily web search. The variable must be named exactly `TAVILY_API_KEY`:

```
TAVILY_API_KEY=
```

Free key (1,000 credits/month): https://app.tavily.com

`load_dotenv()` reads the `.env` in the folder you run from, so `.env` was also copied to `section-02-agent-tools/`.

### 3. Install `uv`

```bash
brew install uv
uv --version      # uv 0.13.5
```

Alternatives: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip3 install uv`.

### 4. Create the project and install dependencies

The folder had no `pyproject.toml`, so `uv sync` from the README would fail. Created one:

```bash
cd section-01-your-first-agent
uv init --bare --no-workspace
uv add python-dotenv langchain-core langchain-openai langchain-ollama
```

This creates `pyproject.toml`, `uv.lock` and `.venv`. Packages match the imports in scripts 01–04.

### 5. Run the scripts

| Script | Command | Result |
|---|---|---|
| 01 | `uv run python 01_hello_world_env_setup.py` | Works. Prints masked `OPENAI_API_KEY`, LangSmith status |
| 02 | `uv run python 02_summary_chain_openai.py` | Failed with OpenAI (`429 insufficient_quota`). Works with Groq (`openai/gpt-oss-120b`) |
| 03 | `uv run python 03_summary_chain_ollama.py` | Works with a local model (`gemma3:270m`) |
| 04 | `uv run python 04_inspect_the_response_object.py --local` | Works. Shows `AIMessage` fields, tokens and metadata |

#### Issue: script 02 — `credit_balance_exhausted`

```
openai.RateLimitError: Error code: 429 ... 'You have no credits remaining.'
```

The key loads and the request reaches OpenAI, but the account has no credit. Fix:

- Add credits at https://platform.openai.com/settings/organization/billing/
- Make sure the credits are in the same organization/project as the key.
- Wait a few minutes after a top-up, then re-run.

#### Issue: script 03 — default model not installed

Ollama was installed, but only `llama3.2` and `smollm2:135m` were pulled; the README default is `gemma3:270m`. Workaround for one run:

```bash
OLLAMA_MODEL=llama3.2 uv run python 03_summary_chain_ollama.py
```

### 6. Download the default Ollama model

```bash
ollama pull gemma3:270m      # about 300 MB
ollama list                  # confirm it is installed
```

The first attempt was cancelled by a command timeout, so it was re-run in the background and completed. `gemma3:270m` (291 MB) is now installed, and script 03 runs with the default model:

```bash
uv run python 03_summary_chain_ollama.py
uv run python 04_inspect_the_response_object.py --local
```

### 7. Switch from OpenAI to Groq (free tier)

OpenAI had no credits, so the scripts were pointed at Groq instead. Groq's API is OpenAI-compatible, so no code change is needed: `ChatOpenAI` reads `OPENAI_API_KEY`, `OPENAI_BASE_URL` and `OPENAI_MODEL` from the environment.

Set these in `.env`:

```
OPENAI_API_KEY=<your Groq key, starts with gsk_>
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=openai/gpt-oss-120b
```

- The variable is still called `OPENAI_API_KEY`, because that is the name the SDK looks up. Its value is the Groq key.
- **Groq is not Grok.** Groq (groq.com) keys start with `gsk_`. Grok (x.ai) keys start with `xai-` and use `https://api.x.ai/v1`. An earlier attempt with the xAI URL failed with `400 Incorrect API key provided` because the key was a Groq key.
- The default model `gpt-5.6-sol` does not exist on Groq, so `OPENAI_MODEL` must be changed.
- Model names depend on the account. List the ones your key can use:
  ```bash
  curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
  ```
  `llama-3.3-70b-versatile` was not available for this key; `openai/gpt-oss-120b` was. Pick a text model that supports tool calling (Section 2 needs it). Ignore the Whisper, Orpheus and prompt-guard models.
- The free tier has rate limits. On a `429`, wait a minute and re-run.
- Keep the key in `.env` only. Do not paste it into chat or commit it.
- To go back to OpenAI: remove `OPENAI_BASE_URL` and set `OPENAI_MODEL=gpt-5.6-sol`.
- `OPENAI_BASE_URL` and `OPENAI_MODEL` were set in `.env` in both `section-01-your-first-agent` and `section-02-agent-tools`. Each folder has its own `.env`, so keys must be set in both.

### 8. Section 2 (in progress)

Section 2 scripts all use `ChatOpenAI`, so they also work with Groq. Scripts 02–04 additionally need `TAVILY_API_KEY`.

Planned setup (the first attempt was cancelled, so check whether it finished):

```bash
cd section-02-agent-tools
uv init --bare --no-workspace
uv add python-dotenv langchain langchain-core langchain-openai tavily-python langchain-tavily pydantic
uv run python 01_agent_with_placeholder_tool.py
```

Script 04 uses structured output (`response_format=AgentAnswer`); not yet tested with Groq.

### 9. Format the code (black and isort)

The course lists `black>=25.1` and `isort>=6.0` as optional formatters (the README also shows `uv run black .` and `uv run isort .`). There is no `requirements.txt`, so they were added as dev dependencies with `uv`:

```bash
cd section-01-your-first-agent
uv add --dev "black>=25.1" "isort>=6.0"
uv run black --check . --exclude '\.venv'
uv run isort --check-only --skip .venv .
```

Installed: `black` 26.10.1 and `isort` 9.0.2. Section 1: all 5 files already pass, nothing to change. The same was done in `section-02-agent-tools`; see [Section 2](#section-2--setup--run-log).

- `--check` / `--check-only` report problems without changing files. Drop them (`uv run black .`, `uv run isort .`) to format on demand.
- Skip `.venv`, or the tools scan every installed package.

### Quick reference

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: dotenv` | Run via `uv run`, not system `python3` |
| `uv: command not found` | `brew install uv` |
| OpenAI 429 `insufficient_quota` | Add credits / check org and project, or switch to Groq (section 7) |
| `400 Incorrect API key` on `api.x.ai` | The key is a Groq (`gsk_`) key; use `https://api.groq.com/openai/v1` |
| Model not found on Groq | Set `OPENAI_MODEL` to a model from the `/models` list for your key |
| Groq `429` rate limit | Free tier limit; wait and re-run |
| Ollama `ConnectionError` | Start Ollama (`ollama serve`) |
| `model 'gemma3:270m' not found` | `ollama pull gemma3:270m` |

---

## Section 2 — Setup & Run Log

A record of the steps taken to get `section-02-agent-tools` (Your First Agent) running on macOS, following [`section-02-agent-tools/README.md`](section-02-agent-tools/README.md). For the earlier setup (`uv`, Ollama, Groq), see [Section 1](#section-1--setup--run-log).

### 1. Check the starting state

The folder had the scripts and a copied `.env`, but:

- no `pyproject.toml`, `uv.lock` or `.venv`, so the README's `uv sync` would fail;
- `OPENAI_API_KEY` and `TAVILY_API_KEY` were empty in this folder's `.env`.

Each folder reads its own `.env` (`load_dotenv()` loads the one in the folder you run from), so keys set in Section 1 do not apply here automatically.

### 2. Copy the working `.env` from Section 1

```bash
cd section-02-agent-tools
cp ../section-01-your-first-agent/.env .env
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

### 3. Create the project and install dependencies

```bash
cd section-02-agent-tools
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

### 4. Run the scripts

| Script | Command | Result |
|---|---|---|
| 01 | `uv run python 01_agent_with_placeholder_tool.py` | Works |
| 02 | `uv run python 02_agent_with_tavily_sdk_tool.py` | Works |
| 03 | `uv run python 03_agent_with_builtin_tavily_tool.py` | Failed on Groq free tier: `413` token limit (still fails with `max_results=3`) |
| 04 | `uv run python 04_agent_with_structured_output.py` | Not re-run after the change; same cause as 03 |

#### Script 01 — placeholder tool

The agent produced 4 messages: question, tool call `search(...)`, the fake tool result (24°C, light drizzle, 78% humidity), final answer. This shows the agent loop without any web access.

#### Script 02 — Tavily SDK tool

Two live `search` calls, then a table of three upcoming AI/developer meetups in Bengaluru with dates, venues and links. Each search result was about 13,000 characters of JSON, which the trace printer shortens to one line. Results change from day to day.

#### Issue: scripts 03 and 04 — `413 rate_limit_exceeded`

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

### 5. Format the code (black and isort)

The course lists `black>=25.1` and `isort>=6.0` as optional formatters. There is no `requirements.txt`, so they were added as dev dependencies with `uv`:

```bash
cd section-02-agent-tools
uv add --dev "black>=25.1" "isort>=6.0"
uv run black --check . --exclude '\.venv'
uv run isort --check-only --skip .venv .
```

Installed: `black` 26.10.1 and `isort` 9.0.2. `black` first wanted to reformat scripts 03 and 04, because the long trailing comment on the `TavilySearch(max_results=3)` line was too long. The comment was moved onto its own line above the call, and both tools now pass with no changes needed. To format on demand: `uv run black .` and `uv run isort .`.

### 6. Not yet verified

- Scripts 03 and 04 running to completion (need higher token limits).
- Script 04's structured output (`response_format=AgentAnswer`) with Groq.

### Quick reference

| Problem | Fix |
|---|---|
| `MissingAPIKeyError` / Tavily 401 | `TAVILY_API_KEY` missing or misspelled in this folder's `.env` |
| `OPENAI_API_KEY` empty | Copy `../section-01-your-first-agent/.env` or paste the key; each folder has its own `.env` |
| `413 rate_limit_exceeded` on Groq | The agent's repeated searches grow the request past 8k tokens/min. `max_results` and smaller models do not fix it; upgrade the plan or use another provider |
| `429` on Groq | Free-tier rate limit; wait a minute and re-run |
| `ModuleNotFoundError` | Run with `uv run`, not system `python3` |
| Runs show up in LangSmith unexpectedly | Set `LANGSMITH_TRACING=false` in `.env` |

---

## Section 3 — Setup & Run Log

A record of the steps taken to merge the old `day1/section-03-agent-memory` into
`section-03-agent-memory` on macOS (Apple Silicon) and
verify both notebooks work. The `day1/…` paths below are the *old* pre-merge location and no longer exist. For earlier setup (AWS credentials, root `.venv`,
root `.env`), see the Section 1 and 2 logs.

---

### 1. Source layout before merge

```
day1/section-03-agent-memory/
├── 01_personalized_memory_mem0.ipynb
├── 01_personalized_memory_mem0_groq.ipynb
├── 02-langgraph-agentcore-memory/
│   ├── math_agent_with_checkpointing.ipynb
│   ├── math_agent_with_checkpointing_groq.ipynb
│   ├── requirements.txt
│   └── requirements-groq.txt
├── .mem0_course/          ← local FAISS store (gitignored)
├── .venv/                 ← broken (missing pip)
├── README.md
├── requirements.txt
└── requirements-groq.txt
```

The target repo had no `section-03-agent-memory` folder at all.

---

### 2. Merge steps

```bash
# create target
mkdir -p section-03-agent-memory/02-langgraph-agentcore-memory

# copy all notebooks and requirements
cp day1/section-03-agent-memory/01_personalized_memory_mem0*.ipynb       section-03-agent-memory/
cp day1/section-03-agent-memory/requirements*.txt                         section-03-agent-memory/
cp day1/section-03-agent-memory/02-langgraph-agentcore-memory/*.ipynb    section-03-agent-memory/02-langgraph-agentcore-memory/
cp day1/section-03-agent-memory/02-langgraph-agentcore-memory/requirements*.txt  section-03-agent-memory/02-langgraph-agentcore-memory/
cp day1/section-03-agent-memory/README.md                                 section-03-agent-memory/

# symlink root .env (single source of truth)
ln -s <workspace>/.env \
      section-03-agent-memory/.env

# remove source
rm -rf day1/section-03-agent-memory
```

`.venv` and `.mem0_course/` were **not** copied — venvs are machine-specific
and the memory store is runtime data.

---

### 3. Create the section venv

Section 3 needs `mem0ai`, which requires `openai<1.110.0` — incompatible with
`langchain-openai` (needs `openai>=2.45.0`) that lives in the root `.venv`.
A **section-isolated venv** avoids the conflict:

```bash
cd section-03-agent-memory
python3 -m venv .venv
.venv/bin/python -m ensurepip --upgrade
.venv/bin/pip install -r requirements.txt \
                      -r 02-langgraph-agentcore-memory/requirements.txt \
                      python-dotenv
```

Packages installed (key ones):

| Package | Version | Used by |
|---|---|---|
| `strands-agents` | 1.62.0 | notebook 1 (Strands agent with memory tool) |
| `strands-agents-tools[mem0-memory]` | 0.8.10 | notebook 1 (mem0 memory tool) |
| `mem0ai` | 0.1.118 | notebook 1 (long-term per-user memory) |
| `faiss-cpu` | 1.15.1 | notebook 1 (local vector store) |
| `ddgs` | 9.16.1 | notebook 1 (DuckDuckGo search tool) |
| `langchain` | 1.4.7 | notebook 2 |
| `langchain-aws` | 1.9.0 | notebook 2 |
| `langgraph` | 1.2.17 | notebook 2 |
| `langgraph-checkpoint-aws` | 1.2.6 | notebook 2 (AgentCore Memory checkpointer) |
| `bedrock-agentcore` | 1.25.0 | notebook 2 |
| `boto3` | 1.43.118 | both notebooks |

---

### 4. `.env` — single source of truth

All section folders now symlink to the root `.env` instead of keeping a copy.
`load_dotenv()` follows symlinks transparently.

```
section-03-agent-memory/.env
  → <workspace>/.env
```

Keys used by section 3:

| Key | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Bedrock (embeddings + LLM for mem0), AgentCore Memory |
| `AWS_DEFAULT_REGION` | `us-east-1` |

---

### 5. Sanity check results

Verified with the section venv:

```
✓ all imports OK  (strands, mem0, faiss, langchain, langgraph, langchain_aws, bedrock_agentcore, boto3)
✓ Bedrock live: 'Hey there friend!'   (Claude Haiku 4.5, us-east-1)
✓ Mem0 FAISS: stored & retrieved → 'Favourite language is Python'
```

---

### 6. Bugs fixed in the section venv

Two bugs in `mem0ai 0.1.118` required patching the installed package directly.
No notebook code was changed.

#### Bug 1 — `temperature` and `top_p` both sent to Anthropic/Bedrock

**Error:**
```
ValidationException: The model returned the following errors:
`temperature` and `top_p` cannot both be specified for this model.
```

**Root cause:** `mem0/llms/aws_bedrock.py` always includes both keys in
`inferenceConfig` when calling the Bedrock Converse API. Claude 4.5 Haiku
rejects this.

**Fix** (two locations, lines 500–508 and 530–538 of `aws_bedrock.py`):
Removed `"topP"` from `inferenceConfig` for Anthropic models.

```python
# Before
"inferenceConfig": {
    "maxTokens": ...,
    "temperature": ...,
    "topP": ...,      # ← removed
}

# After
"inferenceConfig": {
    "maxTokens": ...,
    "temperature": ...,
}
```

#### Bug 2 — FAISS dimension mismatch (`assert d == self.d`)

**Error:**
```
AssertionError  (faiss/class_wrappers.py line 454)
```

**Root cause:** `embedding_model_dims` was set to `1536` in the sanity-check
config, but `amazon.titan-embed-text-v2:0` returns **1024-dimensional**
vectors by default.

**Fix:** Corrected `embedding_model_dims` to `1024` in the config and cleared
the stale FAISS index at `/tmp/mem0_sanity`.

> **Note for notebook 1:** The notebook itself uses `1536` only if it
> explicitly requests `dimensions=1536` from Titan. The default (no
> `dimensions` param) is 1024. Check the notebook config before running if
> you see this error.

---

### 7. Not yet verified

- Notebook 1 (`01_personalized_memory_mem0.ipynb`) run end-to-end.
- Notebook 2 (`math_agent_with_checkpointing.ipynb`) — requires
  `bedrock-agentcore:CreateMemory` and related IAM permissions; creates and
  deletes an AgentCore Memory resource (cost: cents).
- Groq variants of both notebooks.

---

### Quick reference

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: dotenv` | Run with section venv: `.venv/bin/python` |
| `temperature` and `top_p` error | Bug fixed in venv — see Bug 1 above |
| `assert d == self.d` (FAISS) | Check `embedding_model_dims` matches Titan output (default: 1024) |
| `AccessDeniedException` on Bedrock | Check `AWS_ACCESS_KEY_ID` / region in root `.env` |
| `ResourceNotFoundException` (AgentCore) | Account needs AgentCore enabled (Paid-plan AWS) |
| Groq rate limit `413` | Single request too large; shorten or upgrade Groq plan |
