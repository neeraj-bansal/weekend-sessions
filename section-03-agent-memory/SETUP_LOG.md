# Section 3 — Setup & Run Log

A record of the steps taken to merge `day1/section-03-agent-memory` into
`weekend-sessions-main/section-03-agent-memory` on macOS (Apple Silicon) and
verify both notebooks work. For earlier setup (AWS credentials, root `.venv`,
root `.env`), see the Section 1 and 2 logs.

---

## 1. Source layout before merge

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

`weekend-sessions-main/` had no `section-03` folder at all.

---

## 2. Merge steps

```bash
# create target
mkdir -p weekend-sessions-main/section-03-agent-memory/02-langgraph-agentcore-memory

# copy all notebooks and requirements
cp day1/section-03-agent-memory/01_personalized_memory_mem0*.ipynb       weekend-sessions-main/section-03-agent-memory/
cp day1/section-03-agent-memory/requirements*.txt                         weekend-sessions-main/section-03-agent-memory/
cp day1/section-03-agent-memory/02-langgraph-agentcore-memory/*.ipynb    weekend-sessions-main/section-03-agent-memory/02-langgraph-agentcore-memory/
cp day1/section-03-agent-memory/02-langgraph-agentcore-memory/requirements*.txt  weekend-sessions-main/section-03-agent-memory/02-langgraph-agentcore-memory/
cp day1/section-03-agent-memory/README.md                                 weekend-sessions-main/section-03-agent-memory/

# symlink root .env (single source of truth)
ln -s /Users/Shared/Personal/Interview/personal_projects/Scaler/.env \
      weekend-sessions-main/section-03-agent-memory/.env

# remove source
rm -rf day1/section-03-agent-memory
```

`.venv` and `.mem0_course/` were **not** copied — venvs are machine-specific
and the memory store is runtime data.

---

## 3. Create the section venv

Section 3 needs `mem0ai`, which requires `openai<1.110.0` — incompatible with
`langchain-openai` (needs `openai>=2.45.0`) that lives in the root `.venv`.
A **section-isolated venv** avoids the conflict:

```bash
cd weekend-sessions-main/section-03-agent-memory
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

## 4. `.env` — single source of truth

All section folders now symlink to the root `.env` instead of keeping a copy.
`load_dotenv()` follows symlinks transparently.

```
weekend-sessions-main/section-03-agent-memory/.env
  → /Users/Shared/Personal/Interview/personal_projects/Scaler/.env
```

Keys used by section 3:

| Key | Purpose |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Bedrock (embeddings + LLM for mem0), AgentCore Memory |
| `AWS_DEFAULT_REGION` | `us-west-2` |

---

## 5. Sanity check results

Verified with the section venv:

```
✓ all imports OK  (strands, mem0, faiss, langchain, langgraph, langchain_aws, bedrock_agentcore, boto3)
✓ Bedrock live: 'Hey there friend!'   (Claude Haiku 4.5, us-west-2)
✓ Mem0 FAISS: stored & retrieved → 'Favourite language is Python'
```

---

## 6. Bugs fixed in the section venv

Two bugs in `mem0ai 0.1.118` required patching the installed package directly.
No notebook code was changed.

### Bug 1 — `temperature` and `top_p` both sent to Anthropic/Bedrock

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

### Bug 2 — FAISS dimension mismatch (`assert d == self.d`)

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

## 7. Not yet verified

- Notebook 1 (`01_personalized_memory_mem0.ipynb`) run end-to-end.
- Notebook 2 (`math_agent_with_checkpointing.ipynb`) — requires
  `bedrock-agentcore:CreateMemory` and related IAM permissions; creates and
  deletes an AgentCore Memory resource (cost: cents).
- Groq variants of both notebooks.

---

## Quick reference

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: dotenv` | Run with section venv: `.venv/bin/python` |
| `temperature` and `top_p` error | Bug fixed in venv — see Bug 1 above |
| `assert d == self.d` (FAISS) | Check `embedding_model_dims` matches Titan output (default: 1024) |
| `AccessDeniedException` on Bedrock | Check `AWS_ACCESS_KEY_ID` / region in root `.env` |
| `ResourceNotFoundException` (AgentCore) | Account needs AgentCore enabled (Paid-plan AWS) |
| Groq rate limit `413` | Single request too large; shorten or upgrade Groq plan |
