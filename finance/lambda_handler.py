"""AWS Lambda Handler for the 60-Second Multi-Agent Fundamental Stock Analyst.

Handles API Gateway POST /analyze requests:
  Request Body:  {"ticker": "AAPL"}
  Response Body: Complete JSON investment brief and fundamental metrics.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Ensure task root and parent directory are on sys.path
task_root = Path(__file__).resolve().parent
if str(task_root) not in sys.path:
    sys.path.insert(0, str(task_root))
if str(task_root.parent) not in sys.path:
    sys.path.insert(0, str(task_root.parent))

try:
    from finance.agents.orchestrator import run_analysis
except ImportError:
    from agents.orchestrator import run_analysis

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: dict, context: object) -> dict:
    """AWS Lambda entry point for API Gateway events.

    Args:
        event: API Gateway proxy event dictionary.
        context: AWS Lambda runtime context object.

    Returns:
        API Gateway compliant HTTP response dictionary.
    """
    logger.info("Lambda invocation received: %s", json.dumps(event.get("pathParameters") or {}))

    # 1. Parse request body or query parameters
    ticker = "AAPL"
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
            ticker = body.get("ticker", "AAPL")
        elif isinstance(event.get("body"), dict):
            ticker = event["body"].get("ticker", "AAPL")
        elif event.get("queryStringParameters") and "ticker" in event["queryStringParameters"]:
            ticker = event["queryStringParameters"]["ticker"]
        elif event.get("ticker"):
            ticker = event["ticker"]
    except Exception as e:
        logger.warning("Error parsing request body, defaulting to AAPL: %s", str(e))

    ticker_clean = str(ticker).strip().upper()
    logger.info("Processing fundamental research for ticker: %s", ticker_clean)

    # 2. Execute multi-agent 3-phase pipeline asynchronously
    try:
        result = asyncio.run(run_analysis(ticker_clean))
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            },
            "body": json.dumps(result),
        }
    except Exception as e:
        logger.exception("Error during Lambda execution for %s: %s", ticker_clean, str(e))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e), "ticker": ticker_clean}),
        }
