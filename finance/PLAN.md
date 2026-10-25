# Implementation Plan: 60-Second AI Fundamental Stock Analyst

This plan guides the bottom-up development of the multi-agent fundamental analysis system as specified in [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md).

---

## 📅 Roadmap Overview

```
[Phase 1: Tools (Hands)] ➡️ [Phase 2: Agents (Brains)] ➡️ [Phase 3: Orchestration (Manager)] ➡️ [Phase 4: CLI & Testing]
```

---

## Phase 1: Tools Infrastructure & In-Memory Caching ("The Hands")
*Goal: Implement pure deterministic Python functions returning valid JSON strings with caching to eliminate duplicate API requests.*

- [ ] **1.1 Caching Utility (`tools/cache_utils.py` or within tools)**
  - Implement `@cache_tool_result` decorator using `functools` to cache responses based on `(tool_name, args, kwargs)`.
  - Ensures calls like `get_balance_sheet(ticker="AAPL")` and `compute_key_ratios(ticker="AAPL")` resolve in $<1\text{ms}$ when shared between `FinancialDataAgent` and `RiskAgent`.

- [ ] **1.2 Financial Tools (`tools/financial_tools.py`)**
  - `get_income_statement(ticker: str) -> str (JSON)`: Fetches 3-year revenue, gross profit, operating income, net income via `yfinance`.
  - `get_balance_sheet(ticker: str) -> str (JSON)`: Fetches total assets, current assets, current liabilities, total debt, cash, and shareholders' equity.
  - `get_cash_flow_statement(ticker: str) -> str (JSON)`: Fetches operating cash flow, CapEx, free cash flow (FCF), share repurchases, dividends.
  - `compute_key_ratios(ticker: str) -> str (JSON)`: Computes Current Ratio, Quick Ratio, Cash Ratio, Debt/Equity, ROE, ROIC, Gross/Net Margins, and 3-Year CAGR.

- [ ] **1.3 Valuation Tools (`tools/valuation_tools.py`)**
  - `run_dcf_model(ticker: str, growth_rate: float, discount_rate: float, terminal_growth: float) -> str (JSON)`: Computes 5-year FCF projections, terminal value via Gordon Growth, enterprise value, equity value, and DCF intrinsic fair value per share.
  - `get_peer_multiples(ticker: str) -> str (JSON)`: Compares target stock's P/E, EV/EBITDA, and P/B against industry sector median.

- [ ] **1.4 News & Sentiment Tools (`tools/news_tools.py`)**
  - `search_recent_news(ticker: str, company_name: str) -> str (JSON)`: Queries recent business headlines, quarterly earnings commentary, and regulatory updates (via Tavily / DuckDuckGo / yfinance news fallback).
  - `analyze_sentiment(ticker: str) -> str (JSON)`: Summarizes sentiment score (BULLISH / NEUTRAL / BEARISH) with key news catalysts.

---

## Phase 2: Specialist Agent Definitions ("The Brains")
*Goal: Configure individual LLM agents with focused system instructions, output schemas, and specific tool assignments.*

- [ ] **2.1 Financial Data Agent (`agents/financial_data_agent.py`)**
  - Role: Junior Analyst (The Spreadsheet).
  - Assigned Tools: `get_income_statement`, `get_balance_sheet`, `get_cash_flow_statement`, `compute_key_ratios`.
  - Output: Financial health verdict and key metric scorecard.

- [ ] **2.2 News & Sentiment Agent (`agents/news_sentiment_agent.py`)**
  - Role: News Desk Analyst.
  - Assigned Tools: `search_recent_news`, `analyze_sentiment`.
  - Output: Sentiment verdict, competitive moat evaluation, and recent catalysts.

- [ ] **2.3 Risk & Red Team Agent (`agents/risk_agent.py`)**
  - Role: Risk Manager (The Sceptic).
  - Assigned Tools: Shared `get_balance_sheet`, `compute_key_ratios`, `search_recent_news`.
  - Output: Liquidity stress test, debt risk, and top 3 downside risk flags.

- [ ] **2.4 Valuation Agent (`agents/valuation_agent.py`)**
  - Role: Valuation Specialist.
  - Assigned Tools: `run_dcf_model`, `get_peer_multiples`.
  - Input: Uses financial context from Phase 1.
  - Output: Intrinsic value per share, margin of safety, and valuation verdict (`SIGNIFICANTLY OVERVALUED`, `FAIRLY VALUED`, `UNDERVALUED`).

- [ ] **2.5 Report Writer Agent (`agents/report_writer_agent.py`)**
  - Role: Managing Director.
  - Assigned Tools: None (Pure synthesis).
  - Logic: Applies Decision Rating Matrix to reconcile valuation vs. risk vs. sentiment into final recommendation (`STRONG BUY`, `BUY`, `HOLD`, `SELL`, `STRONG SELL`) and structured JSON contract.

---

## Phase 3: Orchestrator & 3-Phase Execution Pipeline ("The Manager")
*Goal: Implement asynchronous multi-agent coordination for sub-60-second execution.*

- [ ] **3.1 Orchestrator Module (`agents/orchestrator.py`)**
  - Wraps the 5 specialist agents as tools using `.as_tool()`.
  - Executes the 3 distinct phases:
    1. **Phase 1 (Parallel)**: Dispatches `FinancialDataAgent`, `NewsAndSentimentAgent`, `RiskAgent` simultaneously using `asyncio.gather`.
    2. **Phase 2 (Sequential)**: Invokes `ValuationAgent` enriched with financial context from Phase 1.
    3. **Phase 3 (Synthesis)**: Feeds all 4 specialist outputs into `ReportWriterAgent` to generate the final Investment Brief and JSON export.

---

## Phase 4: CLI Application, Verification & Testing
*Goal: Provide a single command CLI and verify execution speed and accuracy.*

- [ ] **4.1 CLI Entry Point (`main.py`)**
  - Accepts ticker symbol via command line: `python main.py AAPL`.
  - Measures total execution latency and verifies $<60$s runtime.
  - Prints the formatted 1-Page Investment Brief and outputs the JSON contract to stdout or disk.

- [ ] **4.2 End-to-End Validation & Smoke Test**
  - Test run with `AAPL` and `MSFT`.
  - Validate tool caching hit rates (no duplicate network requests).
  - Validate that the output JSON strictly matches the contract in `PROBLEM_STATEMENT.md`.
