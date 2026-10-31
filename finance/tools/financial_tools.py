"""Financial statement and ratio computation tools.

Every tool adheres to the core rules:
1. Returns a structured JSON string.
2. Numbers arrive as clean numbers (float/int), not formatted strings.
3. Uses in-memory caching to prevent duplicate API fetches between agents.
"""

import json
import logging
import yfinance as yf
from finance.tools.cache_utils import cache_tool_result

logger = logging.getLogger(__name__)


def _clean_series_or_val(val: float | int | None) -> float | None:
    """Helper to sanitize numpy/pandas float or nan into pure python float."""
    if val is None or str(val).lower() == "nan":
        return None
    try:
        f = float(val)
        return round(f, 4)
    except (ValueError, TypeError):
        return None


@cache_tool_result
def get_income_statement(ticker: str) -> str:
    """Fetch the annual Income Statement (Revenue, Gross Profit, Operating Income, Net Income, EPS) for a ticker.

    Args:
        ticker: The stock symbol (e.g. 'AAPL', 'MSFT').

    Returns:
        JSON string containing multi-year income statement data.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        financials = t.financials

        if financials is None or financials.empty:
            return json.dumps({"ticker": ticker, "error": "No income statement data found."})

        data = {}
        for col in financials.columns:
            year_str = str(col.year) if hasattr(col, "year") else str(col)[:4]
            series = financials[col]
            data[year_str] = {
                "total_revenue": _clean_series_or_val(series.get("Total Revenue")),
                "cost_of_revenue": _clean_series_or_val(series.get("Cost Of Revenue")),
                "gross_profit": _clean_series_or_val(series.get("Gross Profit")),
                "operating_income": _clean_series_or_val(series.get("Operating Income")),
                "net_income": _clean_series_or_val(series.get("Net Income")),
                "ebitda": _clean_series_or_val(series.get("EBITDA") or series.get("Normalized EBITDA")),
                "diluted_eps": _clean_series_or_val(series.get("Diluted EPS")),
            }

        return json.dumps({"ticker": ticker.upper(), "income_statement": data}, indent=2)
    except Exception as e:
        logger.error("Error fetching income statement for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})


@cache_tool_result
def get_balance_sheet(ticker: str) -> str:
    """Fetch the annual Balance Sheet (Assets, Liabilities, Cash, Debt, Equity) for a ticker.

    Args:
        ticker: The stock symbol (e.g. 'AAPL', 'MSFT').

    Returns:
        JSON string containing multi-year balance sheet data.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        bs = t.balance_sheet

        if bs is None or bs.empty:
            return json.dumps({"ticker": ticker, "error": "No balance sheet data found."})

        data = {}
        for col in bs.columns:
            year_str = str(col.year) if hasattr(col, "year") else str(col)[:4]
            series = bs[col]
            data[year_str] = {
                "total_assets": _clean_series_or_val(series.get("Total Assets")),
                "current_assets": _clean_series_or_val(series.get("Current Assets")),
                "cash_and_equivalents": _clean_series_or_val(
                    series.get("Cash And Cash Equivalents") or series.get("Cash Financial")
                ),
                "inventory": _clean_series_or_val(series.get("Inventory")),
                "current_liabilities": _clean_series_or_val(series.get("Current Liabilities")),
                "total_debt": _clean_series_or_val(series.get("Total Debt")),
                "long_term_debt": _clean_series_or_val(series.get("Long Term Debt")),
                "stockholders_equity": _clean_series_or_val(
                    series.get("Stockholders Equity") or series.get("Common Stock Equity")
                ),
            }

        return json.dumps({"ticker": ticker.upper(), "balance_sheet": data}, indent=2)
    except Exception as e:
        logger.error("Error fetching balance sheet for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})


@cache_tool_result
def get_cash_flow_statement(ticker: str) -> str:
    """Fetch the annual Cash Flow Statement (Operating Cash Flow, CapEx, FCF, Buybacks, Dividends).

    Args:
        ticker: The stock symbol (e.g. 'AAPL', 'MSFT').

    Returns:
        JSON string containing multi-year cash flow data.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        cf = t.cashflow

        if cf is None or cf.empty:
            return json.dumps({"ticker": ticker, "error": "No cash flow data found."})

        data = {}
        for col in cf.columns:
            year_str = str(col.year) if hasattr(col, "year") else str(col)[:4]
            series = cf[col]
            op_cf = _clean_series_or_val(series.get("Operating Cash Flow"))
            capex = _clean_series_or_val(series.get("Capital Expenditure"))
            fcf = _clean_series_or_val(series.get("Free Cash Flow"))

            # Calculate FCF manually if not provided directly
            if fcf is None and op_cf is not None and capex is not None:
                fcf = round(op_cf - abs(capex), 2)

            data[year_str] = {
                "operating_cash_flow": op_cf,
                "capital_expenditure": capex,
                "free_cash_flow": fcf,
                "common_stock_repurchase": _clean_series_or_val(series.get("Repurchase Of Capital Stock")),
                "cash_dividends_paid": _clean_series_or_val(series.get("Common Stock Dividend Paid")),
            }

        return json.dumps({"ticker": ticker.upper(), "cash_flow_statement": data}, indent=2)
    except Exception as e:
        logger.error("Error fetching cash flow for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})


@cache_tool_result
def compute_key_ratios(ticker: str) -> str:
    """Compute core profitability, liquidity, solvency, and valuation ratios.

    Args:
        ticker: The stock symbol (e.g. 'AAPL', 'MSFT').

    Returns:
        JSON string with profitability, liquidity, leverage, and growth metrics.
    """
    try:
        t = yf.Ticker(ticker.strip().upper())
        info = t.info
        financials = t.financials
        bs = t.balance_sheet

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        # 1. Profitability Metrics
        gross_margin = info.get("grossMargins")
        operating_margin = info.get("operatingMargins")
        net_margin = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")

        # 2. Liquidity Metrics
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")

        # Compute Cash Ratio and Working Capital from latest Balance Sheet
        cash_ratio = None
        working_capital = None
        if bs is not None and not bs.empty:
            latest_bs = bs.iloc[:, 0]
            cash = latest_bs.get("Cash And Cash Equivalents") or latest_bs.get("Cash Financial") or 0
            curr_assets = latest_bs.get("Current Assets") or 0
            curr_liab = latest_bs.get("Current Liabilities") or 1
            if curr_liab:
                cash_ratio = round(float(cash) / float(curr_liab), 4)
                working_capital = round(float(curr_assets) - float(curr_liab), 2)

        # 3. Solvency & Debt Ratios
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
            debt_to_equity = round(debt_to_equity / 100.0 if debt_to_equity > 10 else debt_to_equity, 4)

        # 4. Valuation Multiples
        pe_trailing = info.get("trailingPE")
        pe_forward = info.get("forwardPE")
        pb_ratio = info.get("priceToBook")
        ev_to_ebitda = info.get("enterpriseToEbitda")
        ev_to_revenue = info.get("enterpriseToRevenue")

        # 5. Multi-year Revenue Growth CAGR (3-Year)
        revenue_cagr_3yr = None
        if financials is not None and not financials.empty and len(financials.columns) >= 3:
            try:
                rev_latest = financials.iloc[:, 0].get("Total Revenue")
                rev_old = financials.iloc[:, 2].get("Total Revenue")
                if rev_latest and rev_old and rev_old > 0:
                    revenue_cagr_3yr = round(((float(rev_latest) / float(rev_old)) ** (1.0 / 2.0)) - 1.0, 4)
            except Exception:
                pass

        result = {
            "ticker": ticker.upper(),
            "company_name": info.get("shortName") or info.get("longName"),
            "current_price": current_price,
            "profitability": {
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_profit_margin": net_margin,
                "return_on_equity_roe": roe,
                "return_on_assets_roa": roa,
            },
            "liquidity": {
                "current_ratio": current_ratio,
                "quick_ratio": quick_ratio,
                "cash_ratio": cash_ratio,
                "working_capital_usd": working_capital,
            },
            "solvency": {
                "debt_to_equity": debt_to_equity,
            },
            "valuation_multiples": {
                "pe_trailing": pe_trailing,
                "pe_forward": pe_forward,
                "price_to_book": pb_ratio,
                "ev_to_ebitda": ev_to_ebitda,
                "ev_to_revenue": ev_to_revenue,
            },
            "growth": {
                "revenue_cagr_3yr": revenue_cagr_3yr,
            },
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error("Error computing key ratios for %s: %s", ticker, str(e))
        return json.dumps({"ticker": ticker, "error": str(e)})
