"""News search and sentiment analysis tools for fundamental equity research."""

import json
import logging
import os
import yfinance as yf
from finance.tools.cache_utils import cache_tool_result

logger = logging.getLogger(__name__)


@cache_tool_result
def search_recent_news(ticker: str, max_results: int = 5) -> str:
    """Fetch recent news headlines and summaries for a stock ticker.

    Args:
        ticker: The stock ticker (e.g. 'AAPL', 'MSFT').
        max_results: Maximum number of news stories to retrieve (default: 5).

    Returns:
        JSON string containing news items with title, publisher, link, and summary.
    """
    ticker_clean = ticker.strip().upper()
    articles = []

    # Strategy 1: Try Tavily Search if API key is present
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if tavily_api_key:
        try:
            from tavily import TavilyClient

            tclient = TavilyClient(api_key=tavily_api_key)
            query = f"{ticker_clean} stock earnings financial news"
            tav_res = tclient.search(query=query, search_depth="basic", max_results=max_results)
            for res in tav_res.get("results", []):
                articles.append({
                    "title": res.get("title"),
                    "source": "Tavily Search",
                    "snippet": res.get("content", "")[:300],
                    "url": res.get("url"),
                })
        except Exception as e:
            logger.warning("Tavily search failed, falling back: %s", str(e))

    # Strategy 2: Try DuckDuckGo Search if Tavily yielded no results
    if not articles:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS(timeout=3) as ddgs_client:
                query = f"{ticker_clean} stock earnings news"
                ddg_res = list(ddgs_client.text(query, max_results=max_results))
                for item in ddg_res:
                    articles.append({
                        "title": item.get("title"),
                        "source": "DuckDuckGo Web",
                        "snippet": item.get("body", "")[:300],
                        "url": item.get("href") or item.get("url"),
                    })
        except Exception as e:
            logger.warning("DuckDuckGo search fallback: %s", str(e))

    # Strategy 3: Reliable fallback using yfinance news
    if not articles:
        try:
            t = yf.Ticker(ticker_clean)
            yf_news = t.news
            if yf_news:
                for item in yf_news[:max_results]:
                    content = item.get("content", {})
                    title = content.get("title") or item.get("title")
                    summary = content.get("summary") or item.get("summary") or ""
                    url = (
                        content.get("canonicalUrl", {}).get("url")
                        if isinstance(content.get("canonicalUrl"), dict)
                        else item.get("link")
                    )
                    pub = content.get("provider", {}).get("displayName") or "Yahoo Finance"
                    articles.append({
                        "title": title,
                        "source": pub,
                        "snippet": summary[:300],
                        "url": str(url) if url else "",
                    })
        except Exception as e:
            logger.error("yfinance news fallback error: %s", str(e))

    return json.dumps({
        "ticker": ticker_clean,
        "articles_count": len(articles),
        "articles": articles[:max_results],
    }, indent=2)


@cache_tool_result
def analyze_sentiment(ticker: str) -> str:
    """Analyze news sentiment and key market catalysts for a given ticker.

    Args:
        ticker: The stock ticker (e.g. 'AAPL').

    Returns:
        JSON string containing sentiment score, sentiment mood (BULLISH/NEUTRAL/BEARISH), and catalyst flags.
    """
    ticker_clean = ticker.strip().upper()
    news_json_str = search_recent_news(ticker_clean, max_results=5)
    news_data = json.loads(news_json_str)
    articles = news_data.get("articles", [])

    # Deterministic financial keyword sentiment scoring
    bullish_keywords = [
        "beat", "record", "growth", "surge", "gain", "upgrade", "outperform",
        "profit", "strong", "higher", "positive", "ai", "demand", "dividend"
    ]
    bearish_keywords = [
        "miss", "fall", "drop", "downgrade", "loss", "decline", "weak", "warning",
        "investigation", "lawsuit", "slump", "tariff", "risk", "lower", "headwind"
    ]

    bull_score = 0
    bear_score = 0
    catalysts = []

    for art in articles:
        text = f"{art.get('title', '')} {art.get('snippet', '')}".lower()
        found_bull = [kw for kw in bullish_keywords if kw in text]
        found_bear = [kw for kw in bearish_keywords if kw in text]

        bull_score += len(found_bull)
        bear_score += len(found_bear)

        if found_bull:
            catalysts.append(f"Positive momentum signal: {art.get('title', '')[:70]}")
        if found_bear:
            catalysts.append(f"Downside caution: {art.get('title', '')[:70]}")

    if bull_score > bear_score:
        sentiment = "BULLISH"
    elif bear_score > bull_score:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"

    result = {
        "ticker": ticker_clean,
        "sentiment": sentiment,
        "bullish_signals": bull_score,
        "bearish_signals": bear_score,
        "key_catalysts": catalysts[:4],
    }

    return json.dumps(result, indent=2)
