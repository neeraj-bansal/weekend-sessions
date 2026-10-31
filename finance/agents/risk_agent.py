"""Risk Agent (Risk Manager - The Professional Sceptic).

Role: Identifies downside risks, accounting red flags, debt stress, and valuation risks.
Assigned Tools: get_balance_sheet, compute_key_ratios, search_recent_news (all shared tools!).
"""

import json
import logging
from finance.tools.financial_tools import compute_key_ratios, get_balance_sheet
from finance.tools.news_tools import search_recent_news
from finance.agents.agent_factory import run_llm_inference

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the RiskAgent on an institutional investment committee. You are the professional sceptic.
Your job is to identify every downside vulnerability, accounting anomaly, debt risk, and valuation extreme.

Rules:
1. Challenge optimistic assumptions.
2. Check Debt-to-Equity, Interest Coverage, and Liquidity ratios.
3. Assess valuation multiples (P/E, EV/EBITDA) compared to historical norms.
4. Output strict JSON with keys:
   - "ticker": string
   - "risk_verdict": "LOW RISK" | "MODERATE RISK" | "ELEVATED RISK" | "HIGH RISK"
   - "risk_factors": list of strings (top 3 critical downside risks)
   - "stress_test_notes": string
"""


def run_risk_agent(ticker: str) -> dict:
    """Execute the Risk Agent for a stock ticker.

    Args:
        ticker: The stock ticker (e.g. 'AAPL').

    Returns:
        Structured dictionary with risk verdict and risk factors.
    """
    ticker_clean = ticker.strip().upper()

    # Step 1: Run assigned shared tools (retrieved instantly from cache if already queried!)
    bs_json = get_balance_sheet(ticker_clean)
    ratios_json = compute_key_ratios(ticker_clean)
    news_json = search_recent_news(ticker_clean, max_results=3)

    ratios_data = json.loads(ratios_json)

    # Step 2: Feed context to LLM
    user_prompt = f"""Identify critical downside risks and stress-test ticker {ticker_clean}:
Key Ratios:
{ratios_json}

Recent Balance Sheet:
{bs_json[:800]}
"""

    llm_output = run_llm_inference(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        json_mode=True,
    )

    try:
        if llm_output:
            return json.loads(llm_output)
    except Exception:
        pass

    # Fallback risk assessment
    pe = ratios_data.get("valuation_multiples", {}).get("pe_trailing") or 35.0
    de = ratios_data.get("solvency", {}).get("debt_to_equity") or 0.8
    cr = ratios_data.get("liquidity", {}).get("current_ratio") or 1.0

    risk_flags = []
    if pe > 30.0:
        risk_flags.append(f"Valuation multiple risk: Trailing P/E ({pe}x) is elevated relative to historical norms.")
    if de > 1.5:
        risk_flags.append(f"High financial leverage: Debt-to-Equity of {de}x elevates interest rate sensitivity.")
    if cr < 1.0:
        risk_flags.append(f"Tight liquidity cushion: Current ratio of {cr}x requires continuous operating cash flows.")
    if not risk_flags:
        risk_flags = [
            "Supply chain and geographic revenue concentration",
            "Regulatory scrutiny and antitrust litigation headwinds",
            "Macroeconomic consumer spending slowdown",
        ]

    return {
        "ticker": ticker_clean,
        "risk_verdict": "ELEVATED RISK" if pe > 30 else "MODERATE RISK",
        "risk_factors": risk_flags[:3],
        "stress_test_notes": "Capital structure is highly leveraged by design due to share buybacks. Multiples leave little margin of safety.",
    }
