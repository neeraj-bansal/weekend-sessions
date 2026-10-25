"""FastAPI Cloud Service & Serverless Handler for the Fundamental Analysis System.

Exposes REST endpoints:
  - GET  /health           : Health check endpoint
  - POST /analyze          : Run multi-agent fundamental analysis for a ticker
"""

import asyncio
import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from finance.agents.orchestrator import run_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="60-Second AI Fundamental Stock Analyst API",
    description="Multi-Agent Equity Research Service powered by Strands & Bedrock / Groq / OpenAI",
    version="1.0.0",
)


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL, MSFT, NVDA)", example="AAPL")


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestrators (ECS / Kubernetes / ALB)."""
    return {"status": "healthy", "service": "finance-multi-agent-analyst"}


@app.get("/analyze/{ticker}")
async def analyze_get(ticker: str) -> dict[str, Any]:
    """Analyze stock fundamentals via GET endpoint."""
    try:
        ticker_clean = ticker.strip().upper()
        result = await run_analysis(ticker_clean)
        return result
    except Exception as e:
        logger.exception("Error analyzing ticker %s: %s", ticker, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_post(request: AnalysisRequest) -> dict[str, Any]:
    """Analyze stock fundamentals via POST JSON request."""
    try:
        ticker_clean = request.ticker.strip().upper()
        result = await run_analysis(ticker_clean)
        return result
    except Exception as e:
        logger.exception("Error analyzing ticker %s: %s", request.ticker, str(e))
        raise HTTPException(status_code=500, detail=str(e))


# AWS Lambda Handler adapter (if deployed to AWS Lambda + API Gateway)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
