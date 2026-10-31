"""In-memory caching utility for financial tools to prevent duplicate API requests."""

import functools
import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Global in-memory tool cache dictionary
_TOOL_CACHE: dict[str, Any] = {}


def cache_tool_result(func: Callable) -> Callable:
    """Decorator to cache tool function results based on function name and arguments.

    When multiple agents (e.g. FinancialDataAgent and RiskAgent) call the same tool
    for the same stock ticker, the second call returns from cache in <1ms without
    triggering duplicate external HTTP requests.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create a deterministic cache key
        norm_kwargs = tuple(sorted((k, str(v)) for k, v in kwargs.items()))
        norm_args = tuple(str(a) for a in args)
        cache_key = f"{func.__name__}::{norm_args}::{norm_kwargs}"

        if cache_key in _TOOL_CACHE:
            logger.info("Tool Cache HIT: %s", cache_key)
            return _TOOL_CACHE[cache_key]

        logger.info("Tool Cache MISS (fetching live): %s", cache_key)
        result = func(*args, **kwargs)
        _TOOL_CACHE[cache_key] = result
        return result

    return wrapper


def clear_tool_cache() -> None:
    """Clear all cached tool results."""
    _TOOL_CACHE.clear()
