"""Main CLI Entry Point: 60-Second AI Fundamental Stock Analyst.

Usage:
    python main.py AAPL
    python main.py MSFT --json
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Ensure package imports work regardless of where script is launched
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from finance.agents.orchestrator import run_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
# Silence verbose third-party loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="60-Second Autonomous Multi-Agent Fundamental Stock Analyst"
    )
    parser.add_argument(
        "ticker",
        nargs="?",
        default="AAPL",
        help="Stock ticker symbol (e.g. AAPL, MSFT, NVDA, GOOGL)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print pure machine-readable JSON output",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Path to save output JSON report file",
    )
    return parser.parse_args()


async def main_async() -> int:
    args = parse_args()
    ticker = args.ticker.strip().upper()

    print("\n" + "=" * 80)
    print(f"🚀 Launching 60-Second Multi-Agent Equity Research Team for [{ticker}]")
    print("=" * 80)

    try:
        start_wall = time.time()
        result = await run_analysis(ticker)
        wall_time = round(time.time() - start_wall, 2)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            brief = result.get("executive_brief_text", "")
            print("\n" + brief)

            print("\n📊 TELEMETRY & LATENCY METRICS:")
            telemetry = result.get("telemetry", {})
            print(f"  • Phase 1 (Parallel Ingestion & Specialists): {telemetry.get('phase1_parallel_seconds', 0)}s")
            print(f"  • Phase 2 (DCF Valuation Modeling):          {telemetry.get('phase2_valuation_seconds', 0)}s")
            print(f"  • Phase 3 (Synthesis & Brief Generation):    {telemetry.get('phase3_synthesis_seconds', 0)}s")
            print(f"  • Total End-to-End Execution Time:           {wall_time}s")
            status_icon = "✅ SUCCESS (<60s)" if wall_time < 60.0 else "⚠️ EXCEEDED 60s"
            print(f"  • Performance SLA:                           {status_icon}")

        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved structured JSON report to: {args.save}")

        return 0
    except Exception as e:
        logging.exception("Fatal error during analysis of %s: %s", ticker, str(e))
        return 1


def main() -> None:
    exit_code = asyncio.run(main_async())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
