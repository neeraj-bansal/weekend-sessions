# Section 1 — Setup & Run Log

A record of the steps taken to get `day1/section1` working on macOS (Apple Silicon), following [`README.md`](README.md).

## 1. Create the `.env` file

The README says `cp .env.example .env`, but the folder had no `.env.example`, so one was created first.

`.env.example` contents (keys left empty):

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

# Required for day1/section2 scripts 02-04 (free key: https://app.tavily.com)
TAVILY_API_KEY=
```

```bash
cd day1/section1
cp .env.example .env
```

Then paste your real `OPENAI_API_KEY` into `.env`.

> Never commit `.env`. Add it to `.gitignore` if the folder is ever put under git.

## 2. Add the Tavily key (needed by Section 2)

Section 2 scripts 02–04 call Tavily web search. The variable must be named exactly `TAVILY_API_KEY`:

```
TAVILY_API_KEY=
```

Free key (1,000 credits/month): https://app.tavily.com

`load_dotenv()` reads the `.env` in the folder you run from, so `.env` and `.env.example` were also copied to `day1/section2/`.

## 3. Install `uv`

```bash
brew install uv
uv --version      # uv 0.13.5
```

Alternatives: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip3 install uv`.

## 4. Create the project and install dependencies

The folder had no `pyproject.toml`, so `uv sync` from the README would fail. Created one:

```bash
cd day1/section1
uv init --bare --no-workspace
uv add python-dotenv langchain-core langchain-openai langchain-ollama
```

This creates `pyproject.toml`, `uv.lock` and `.venv`. Packages match the imports in scripts 01–04.

## 5. Run the scripts

| Script | Command | Result |
|---|---|---|
| 01 | `uv run python 01_hello_world_env_setup.py` | Works. Prints masked `OPENAI_API_KEY`, LangSmith status |
| 02 | `uv run python 02_summary_chain_openai.py` | Failed with OpenAI (`429 insufficient_quota`). Works with Groq (`openai/gpt-oss-120b`) |
| 03 | `uv run python 03_summary_chain_ollama.py` | Works with a local model (`gemma3:270m`) |
| 04 | `uv run python 04_inspect_the_response_object.py --local` | Works. Shows `AIMessage` fields, tokens and metadata |

### Issue: script 02 — `credit_balance_exhausted`

```
openai.RateLimitError: Error code: 429 ... 'You have no credits remaining.'
```

The key loads and the request reaches OpenAI, but the account has no credit. Fix:

- Add credits at https://platform.openai.com/settings/organization/billing/
- Make sure the credits are in the same organization/project as the key.
- Wait a few minutes after a top-up, then re-run.

### Issue: script 03 — default model not installed

Ollama was installed, but only `llama3.2` and `smollm2:135m` were pulled; the README default is `gemma3:270m`. Workaround for one run:

```bash
OLLAMA_MODEL=llama3.2 uv run python 03_summary_chain_ollama.py
```

## 6. Download the default Ollama model

```bash
ollama pull gemma3:270m      # about 300 MB
ollama list                  # confirm it is installed
```

The first attempt was cancelled by a command timeout, so it was re-run in the background and completed. `gemma3:270m` (291 MB) is now installed, and script 03 runs with the default model:

```bash
uv run python 03_summary_chain_ollama.py
uv run python 04_inspect_the_response_object.py --local
```

## 7. Switch from OpenAI to Groq (free tier)

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
- `OPENAI_BASE_URL` and `OPENAI_MODEL` were set in `.env` in both `section1` and `section2`. Each folder has its own `.env`, so keys must be set in both.

## 8. Section 2 (in progress)

Section 2 scripts all use `ChatOpenAI`, so they also work with Groq. Scripts 02–04 additionally need `TAVILY_API_KEY`.

Planned setup (the first attempt was cancelled, so check whether it finished):

```bash
cd day1/section2
uv init --bare --no-workspace
uv add python-dotenv langchain langchain-core langchain-openai tavily-python langchain-tavily pydantic
uv run python 01_agent_with_placeholder_tool.py
```

Script 04 uses structured output (`response_format=AgentAnswer`); not yet tested with Groq.

## 9. Format the code (black and isort)

The course lists `black>=25.1` and `isort>=6.0` as optional formatters (the README also shows `uv run black .` and `uv run isort .`). There is no `requirements.txt`, so they were added as dev dependencies with `uv`:

```bash
cd day1/section1
uv add --dev "black>=25.1" "isort>=6.0"
uv run black --check . --exclude '\.venv'
uv run isort --check-only --skip .venv .
```

Installed: `black` 26.10.1 and `isort` 9.0.2. Section 1: all 5 files already pass, nothing to change. The same was done in `day1/section2`; see [`../section2/SETUP_LOG.md`](../section2/SETUP_LOG.md).

- `--check` / `--check-only` report problems without changing files. Drop them (`uv run black .`, `uv run isort .`) to format on demand.
- Skip `.venv`, or the tools scan every installed package.

## Quick reference

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
