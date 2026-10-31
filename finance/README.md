# 60-Second AI Fundamental Stock Analyst 📈

An autonomous multi-agent equity research team in code that performs institutional-grade fundamental stock analysis in **under 60 seconds**.

* 📋 [**`PROBLEM_STATEMENT.md`**](PROBLEM_STATEMENT.md): Full system specification, financial formulas, and architecture.
* 🎓 [**`LEARN_AND_COLLABORATE.md`**](LEARN_AND_COLLABORATE.md): Learning guide and how to interact with Bob for maximum intuition.
* 🗺️ [**`PLAN.md`**](PLAN.md): Step-by-step implementation roadmap across Phases 1 through 4.
* ☁️ [**`DEPLOYMENT.md`**](DEPLOYMENT.md): Cloud deployment blueprint (Bedrock AgentCore, ECS Fargate, AWS Lambda).

---

## ⚡ Quickstart

### 1. Installation

```bash
cd weekend-sessions-main/finance
pip install -r requirements.txt
```

### 2. Environment Configuration

Create or update your `.env` in the project root:

```bash
# Model provider options:
GROQ_API_KEY="gsk_..."         # Groq API Key
# or AWS Bedrock credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# or OPENAI_API_KEY / ANTHROPIC_API_KEY

# Optional web search for news desk:
TAVILY_API_KEY="tvly-..."
```

### 3. Run the Fundamental Analysis CLI

```bash
python main.py AAPL
```

---

## 🏗️ Architecture & Directory Overview

```text
weekend-sessions-main/finance/
├── PROBLEM_STATEMENT.md      # Full specification, financial terms & architecture
├── README.md                 # This quickstart guide
├── requirements.txt          # Python dependencies
├── agents/                   # Multi-agent brain modules
│   ├── financial_data_agent.py   # Statements + ratios -> financial health verdict
│   ├── news_sentiment_agent.py   # Headlines -> sentiment verdict + risk flags
│   ├── risk_agent.py             # Sceptic: risk register + liquidity stress test
│   ├── valuation_agent.py        # DCF + peer multiples -> valuation verdict
│   ├── report_writer_agent.py    # Final investment memo synthesis (no tools)
│   └── orchestrator.py           # 3-phase workflow manager
├── tools/                    # Plain Python tools returning JSON (with in-memory caching)
│   ├── financial_tools.py        # Statements & ratio computation
│   ├── valuation_tools.py        # DCF & peer multiples
│   └── news_tools.py             # Search & sentiment analysis
└── main.py                   # CLI entry point
```

---

## 📖 Key Principles (Bottom-Up)
1. **Tools are the Hands**: Pure Python functions that fetch and calculate deterministic numbers. Every tool returns a JSON string and uses in-memory caching.
2. **Agents are the Brains**: LLMs with strict instructions and assigned tools.
3. **Orchestrator is the Manager**: Dispatches parallel calls across Phase 1 (`FinancialDataAgent`, `NewsAndSentimentAgent`, `RiskAgent`), feeds context into Phase 2 (`ValuationAgent`), and synthesizes in Phase 3 (`ReportWriterAgent`).
