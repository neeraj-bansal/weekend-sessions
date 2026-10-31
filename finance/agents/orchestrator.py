"""Orchestrator Agent (Director of Research).

Coordinates the 3-phase multi-agent fundamental analysis pipeline:
  Phase 1: Concurrent execution of FinancialDataAgent, NewsAndSentimentAgent, and RiskAgent.
  Phase 2: Execution of ValuationAgent with financial context.
  Phase 3: Final synthesis by ReportWriterAgent to generate the 1-Page Brief and JSON contract.
"""

import asyncio
import logging
import time
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from finance.agents.financial_data_agent import run_financial_data_agent
from finance.agents.news_sentiment_agent import run_news_sentiment_agent
from finance.agents.risk_agent import run_risk_agent
from finance.agents.valuation_agent import run_valuation_agent
from finance.agents.report_writer_agent import run_report_writer_agent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Director of Research Orchestrator that manages the 3-phase research pipeline."""

    def __init__(self, max_workers: int = 4) -> None:
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def analyze(self, ticker: str) -> dict[str, Any]:
        """Execute the full 3-Phase fundamental analysis workflow on a ticker.

        Args:
            ticker: Stock ticker symbol (e.g. 'AAPL', 'MSFT').

        Returns:
            Dictionary containing the complete investment memo, JSON contract, and phase timings.
        """
        ticker_clean = ticker.strip().upper()
        start_time = time.time()
        loop = asyncio.get_running_loop()

        logger.info("Starting 3-Phase Fundamental Analysis for %s...", ticker_clean)

        # -------------------------------------------------------------
        # Phase 1: Parallel Execution (Three calls at once)
        # -------------------------------------------------------------
        p1_start = time.time()
        logger.info("Phase 1: Dispatching Financial, News, and Risk agents concurrently...")

        fda_task = loop.run_in_executor(self.executor, run_financial_data_agent, ticker_clean)
        nsa_task = loop.run_in_executor(self.executor, run_news_sentiment_agent, ticker_clean)
        ra_task = loop.run_in_executor(self.executor, run_risk_agent, ticker_clean)

        financial_report, news_report, risk_report = await asyncio.gather(
            fda_task, nsa_task, ra_task
        )
        p1_duration = round(time.time() - p1_start, 2)
        logger.info("Phase 1 completed in %.2fs", p1_duration)

        # -------------------------------------------------------------
        # Phase 2: Valuation Modeling (With Financial Context)
        # -------------------------------------------------------------
        p2_start = time.time()
        logger.info("Phase 2: Running DCF Intrinsic Valuation Agent...")

        valuation_report = await loop.run_in_executor(
            self.executor, run_valuation_agent, ticker_clean
        )
        p2_duration = round(time.time() - p2_start, 2)
        logger.info("Phase 2 completed in %.2fs", p2_duration)

        # -------------------------------------------------------------
        # Phase 3: Synthesis & Investment Brief Generation
        # -------------------------------------------------------------
        p3_start = time.time()
        logger.info("Phase 3: ReportWriterAgent synthesizing final Investment Brief...")

        final_memo = await loop.run_in_executor(
            self.executor,
            run_report_writer_agent,
            ticker_clean,
            financial_report,
            news_report,
            risk_report,
            valuation_report,
        )
        p3_duration = round(time.time() - p3_start, 2)
        total_duration = round(time.time() - start_time, 2)
        logger.info("Phase 3 completed in %.2fs. Total pipeline time: %.2fs", p3_duration, total_duration)

        # Attach telemetry metrics
        final_memo["telemetry"] = {
            "total_execution_seconds": total_duration,
            "phase1_parallel_seconds": p1_duration,
            "phase2_valuation_seconds": p2_duration,
            "phase3_synthesis_seconds": p3_duration,
            "target_under_60s": total_duration < 60.0,
        }

        return final_memo


async def run_analysis(ticker: str) -> dict[str, Any]:
    """Convenience entry point to run the orchestrator."""
    orchestrator = OrchestratorAgent()
    return await orchestrator.analyze(ticker)
