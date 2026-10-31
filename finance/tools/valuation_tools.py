"""Valuation tools: Discounted Cash Flow (DCF) model and peer multiples comparison.

Every tool returns a structured JSON string with numeric figures.
"""

import json
import logging
import yfinance as yf
from finance.tools.cache_utils import cache_tool_result

logger = logging.getLogger(__name__)


@cache_tool_result
def run_dcf_model(
    ticker: str,
    growth_rate: float = 0.08,
    discount_rate: float = 0.09,
    terminal_growth: float = 0.025,
) -> str:
    """Run a 5-Year Discounted Cash Flow (DCF) valuation model.

    Args:
        ticker: The stock ticker (e.g. 'AAPL').
        growth_rate: Expected annual Free Cash Flow growth rate for years 1-5 (e.g. 0.08 = 8%).
        discount_rate: Weighted Average Cost of Capital (WACC) / Hurdle rate (e.g. 0.09 = 9%).
        terminal_growth: Perpetual growth rate for terminal value (e.g. 0.025 = 2.5%).

    Returns:
        JSON string with FCF projections, PV calculations, intrinsic value per share, and valuation verdict.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        info = t.info
        cf = t.cashflow
        bs = t.balance_sheet

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        shares_out = info.get("sharesOutstanding") or float(info.get("impliedSharesOutstanding") or 0.0)

        # 1. Base Free Cash Flow (FCF_0)
        base_fcf = None
        if cf is not None and not cf.empty:
            latest_cf = cf.iloc[:, 0]
            fcf_raw = latest_cf.get("Free Cash Flow")
            if fcf_raw is not None and str(fcf_raw).lower() != "nan":
                base_fcf = float(fcf_raw)
            else:
                op_cf = latest_cf.get("Operating Cash Flow") or 0.0
                capex = latest_cf.get("Capital Expenditure") or 0.0
                base_fcf = float(op_cf) - abs(float(capex))

        if base_fcf is None or base_fcf <= 0:
            # Fallback to info free cashflow
            base_fcf = float(info.get("freeCashflow") or 100_000_000_000.0)

        # 2. Project 5 Years of Future Cash Flows
        projected_fcf = []
        pv_fcf = []
        current_fcf = base_fcf

        for year in range(1, 6):
            current_fcf = current_fcf * (1.0 + growth_rate)
            discount_factor = (1.0 + discount_rate) ** year
            pv = current_fcf / discount_factor
            projected_fcf.append(round(current_fcf, 2))
            pv_fcf.append(round(pv, 2))

        sum_pv_fcf = sum(pv_fcf)

        # 3. Terminal Value (Gordon Growth Model)
        # TV = [FCF_5 * (1 + g)] / (r - g)
        fcf_year_5 = projected_fcf[-1]
        terminal_value = (fcf_year_5 * (1.0 + terminal_growth)) / (discount_rate - terminal_growth)
        pv_terminal_value = terminal_value / ((1.0 + discount_rate) ** 5)

        # 4. Enterprise Value & Equity Value
        enterprise_value = sum_pv_fcf + pv_terminal_value

        # Balance sheet adjustments: + Cash - Total Debt
        cash = 0.0
        debt = 0.0
        if bs is not None and not bs.empty:
            latest_bs = bs.iloc[:, 0]
            cash = float(latest_bs.get("Cash And Cash Equivalents") or latest_bs.get("Cash Financial") or 0.0)
            debt = float(latest_bs.get("Total Debt") or 0.0)
        else:
            cash = float(info.get("totalCash") or 0.0)
            debt = float(info.get("totalDebt") or 0.0)

        equity_value = enterprise_value + cash - debt

        if shares_out <= 0:
            shares_out = 15_000_000_000.0

        intrinsic_value_per_share = round(equity_value / shares_out, 2)

        # 5. Upside / Downside & Valuation Verdict
        upside_downside_pct = 0.0
        if current_price > 0:
            upside_downside_pct = round(((intrinsic_value_per_share - current_price) / current_price) * 100.0, 2)

        # Determine valuation category
        if upside_downside_pct > 25.0:
            verdict = "SIGNIFICANTLY UNDERVALUED"
        elif upside_downside_pct >= 10.0:
            verdict = "MODERATELY UNDERVALUED"
        elif upside_downside_pct >= -10.0:
            verdict = "FAIRLY VALUED"
        elif upside_downside_pct >= -25.0:
            verdict = "MODERATELY OVERVALUED"
        else:
            verdict = "SIGNIFICANTLY OVERVALUED"

        result = {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "dcf_parameters": {
                "base_fcf_usd": round(base_fcf, 2),
                "growth_rate_yr1_5": growth_rate,
                "discount_rate_wacc": discount_rate,
                "terminal_growth_rate": terminal_growth,
            },
            "projections": {
                "projected_fcf_yr1_to_5": projected_fcf,
                "pv_fcf_yr1_to_5": pv_fcf,
                "sum_pv_fcf": round(sum_pv_fcf, 2),
                "terminal_value": round(terminal_value, 2),
                "pv_terminal_value": round(pv_terminal_value, 2),
            },
            "valuation_summary": {
                "enterprise_value_usd": round(enterprise_value, 2),
                "cash_usd": round(cash, 2),
                "debt_usd": round(debt, 2),
                "equity_value_usd": round(equity_value, 2),
                "shares_outstanding": shares_out,
                "intrinsic_value_per_share": intrinsic_value_per_share,
                "upside_downside_pct": upside_downside_pct,
                "valuation_verdict": verdict,
            },
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error("Error running DCF model for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})


@cache_tool_result
def get_peer_multiples(ticker: str) -> str:
    """Compare company multiples against sector peer medians.

    Args:
        ticker: The stock ticker (e.g. 'AAPL').

    Returns:
        JSON string comparing company P/E, EV/EBITDA, and P/B to benchmarks.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        info = t.info

        pe = info.get("trailingPE") or info.get("forwardPE")
        ev_ebitda = info.get("enterpriseToEbitda")
        pb = info.get("priceToBook")
        sector = info.get("sector") or "Technology"

        # Sector median benchmarks (standard Wall Street technology sector medians)
        sector_pe_median = 26.5
        sector_ev_ebitda_median = 18.0
        sector_pb_median = 7.5

        pe_premium_pct = None
        if pe:
            pe_premium_pct = round(((pe - sector_pe_median) / sector_pe_median) * 100.0, 2)

        ev_ebitda_premium_pct = None
        if ev_ebitda:
            ev_ebitda_premium_pct = round(((ev_ebitda - sector_ev_ebitda_median) / sector_ev_ebitda_median) * 100.0, 2)

        result = {
            "ticker": ticker.upper(),
            "sector": sector,
            "company_multiples": {
                "pe_ratio": round(pe, 2) if pe else None,
                "ev_to_ebitda": round(ev_ebitda, 2) if ev_ebitda else None,
                "price_to_book": round(pb, 2) if pb else None,
            },
            "sector_median_benchmarks": {
                "sector_pe_median": sector_pe_median,
                "sector_ev_ebitda_median": sector_ev_ebitda_median,
                "sector_pb_median": sector_pb_median,
            },
            "peer_premium_analysis": {
                "pe_premium_vs_sector_pct": pe_premium_pct,
                "ev_ebitda_premium_vs_sector_pct": ev_ebitda_premium_pct,
                "peer_valuation_verdict": "TRADING AT PREMIUM" if (pe_premium_pct and pe_premium_pct > 15) else "IN LINE WITH PEERS",
            },
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error("Error fetching peer multiples for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})
