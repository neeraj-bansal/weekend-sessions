# Section 1 — Your First AI Agent

Build your first agents on Amazon Bedrock **and** LangChain foundations.

---

## Notebooks & scripts

| File | What it does | Framework |
|---|---|---|
| `01_hello_agent.ipynb` | **Start here (Bedrock).** Model choice → one-line agent → your own tool → a prebuilt tool → system prompt | Strands |
| `01_hello_agent_groq.ipynb` | Same as above but on Groq (no AWS needed) | Strands + Groq |
| `hello_agent.py` | Smallest possible Strands agent as a script | Strands |
| `hello_agent_groq.py` | Same on Groq | Strands + Groq |
| `hello_langgraph_agent.py` | ReAct agent with one tool (`create_agent`) | LangGraph |
| `hello_langgraph_agent_groq.py` | Same on Groq | LangGraph + Groq |
| `01_hello_world_env_setup.py` | Loading keys from `.env` safely (prints a masked key) | LangChain |
| `02_summary_chain_openai.py` | Your first chain: `PromptTemplate \| ChatOpenAI` | LangChain |
| `03_summary_chain_ollama.py` | Same chain on a local model — one-line change | LangChain + Ollama |
| `04_inspect_the_response_object.py` | Every field of the returned `AIMessage` | LangChain |
| `sample_data.py` | Biography text used by every LangChain script | — |
| `aws_strands/test_strands.py` | Minimal Strands + Bedrock smoke test | Strands |

---

## Setup

### Option A — Bedrock (default)

```bash
pip install -r requirements.txt
# or with uv:
uv sync
```

Needs AWS credentials with Bedrock access (`us-west-2` recommended).

### Option B — Groq (no AWS account needed)

```bash
pip install -r requirements-groq.txt
export GROQ_API_KEY=gsk_...   # or put it in .env
```

The default model is `openai/gpt-oss-120b`; set `GROQ_MODEL_ID` in `.env` to use another.

### Option C — Ollama (local, script 03 and `04 --local`)

1. Install Ollama from https://ollama.com/download and start it.
2. `ollama pull gemma3:270m` (~300 MB). Optional better model: `ollama pull gemma4`.

---

## Run

```bash
# Notebooks
jupyter lab 01_hello_agent.ipynb
jupyter lab 01_hello_agent_groq.ipynb

# Strands scripts
python hello_agent.py
python hello_agent_groq.py
python hello_langgraph_agent.py
python hello_langgraph_agent_groq.py

# LangChain scripts
uv run python 01_hello_world_env_setup.py
uv run python 02_summary_chain_openai.py
uv run python 03_summary_chain_ollama.py
uv run python 04_inspect_the_response_object.py           # OpenAI/Groq
uv run python 04_inspect_the_response_object.py --local   # Ollama
```

---

## Strands vs LangChain vs LangGraph

| | Strands Agents | LangChain | LangGraph |
|---|---|---|---|
| Approach | Agent-first SDK: model + tools + prompt | Building blocks: prompts, parsers, loaders, integrations | Stateful graph orchestration |
| Boilerplate | Minimal | Moderate | More setup, more control |
| State | Built in (+ AgentCore Memory / session managers) | Manual | Built in with checkpointers |
| Best for | Fast, AWS-native agents | RAG pipelines and integrations | Complex flows with loops, branches, human-in-the-loop |

```
Need an agent fast on AWS?                    → Strands
Need a simple LLM chain (no agent loop)?      → LangChain
Need complex orchestration or multi-agent?    → LangGraph (or Strands graph/swarm — Section 4)
Need persistent state across sessions?        → LangGraph or Strands, with AgentCore Memory (Section 3)
Going to production on AWS?                   → Either, deployed on AgentCore Runtime (Section 6)
```

---

## How the LangChain chain works

```
{"information": "<bio text>"}
          │
          ▼
  PromptTemplate      fills {information} into the template
          │
          ▼
  ChatOpenAI / ChatOllama    sends the prompt to the model
          │
          ▼
  AIMessage           .text = the answer, .usage_metadata = tokens, …
```

- `load_dotenv()` copies each `KEY=value` line from `.env` into the environment.
- `prompt | llm` builds a **RunnableSequence**. `chain.invoke({...})` runs it once.
- Use `.text` not `.content` — newer models return `.content` as a list of blocks.

---

## Optional: LangSmith tracing

Add to `.env` and re-run any script:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=section-01-your-first-agent
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `OPENAI_API_KEY is missing` | Run `cp .env.example .env` and paste your key |
| `AuthenticationError` / 401 | Key is wrong or revoked — create a new one |
| `model … does not exist` | Set `OPENAI_MODEL=` in `.env` to a model your account can use |
| Ollama `ConnectionError` | Start Ollama (`ollama serve`) |
| `model 'gemma3:270m' not found` | Run `ollama pull gemma3:270m` |

---

**Next:** [Section 2 — Agent Tools](../section-02-agent-tools/README.md)
