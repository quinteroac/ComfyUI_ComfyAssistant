"""
Web search provider abstraction with fallback chain.

Tries SearXNG (if SEARXNG_URL is set) then falls back to DuckDuckGo.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger("ComfyUI_ComfyAssistant.web_search")


async def _search_searxng(
    query: str,
    max_results: int = 5,
    time_range: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Search using a SearXNG instance.

    Requires SEARXNG_URL env var to be set.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
        time_range: Optional time filter (day, week, month, year).

    Returns:
        List of result dicts with title, url, snippet keys.

    Raises:
        RuntimeError: If SEARXNG_URL is not set or the request fails.
    """
    searxng_url = os.environ.get("SEARXNG_URL", "").rstrip("/")
    if not searxng_url:
        raise RuntimeError("SEARXNG_URL not configured")

    params: Dict[str, Any] = {
        "q": query,
        "format": "json",
        "categories": "general",
    }
    if time_range:
        params["time_range"] = time_range

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{searxng_url}/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except Exception as e:
        raise RuntimeError(f"SearXNG request failed: {e}") from e

    results: List[Dict[str, str]] = []
    for item in data.get("results", [])[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        })
    return results


async def _search_duckduckgo(
    query: str,
    max_results: int = 5,
    time_range: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Search using DuckDuckGo (free, no API key).

    Uses the ddgs package (duckduckgo-search is supported for backward
    compatibility). The sync DDGS().text() call is run in an executor
    to avoid blocking the event loop.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.
        time_range: Optional time filter (day, week, month, year).

    Returns:
        List of result dicts with title, url, snippet keys.

    Raises:
        RuntimeError: If the search fails or package is unavailable.
    """
    try:
        from ddgs import DDGS  # type: ignore
        provider_label = "ddgs"
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore
            provider_label = "duckduckgo-search"
            logger.warning(
                "duckduckgo-search is deprecated; install ddgs instead"
            )
        except ImportError as e:
            raise RuntimeError(
                "ddgs package not installed. Run: pip install ddgs"
            ) from e

    # Map time_range to DDG timelimit values
    timelimit_map = {
        "day": "d",
        "week": "w",
        "month": "m",
        "year": "y",
    }
    timelimit = timelimit_map.get(time_range or "", None)

    def _sync_search() -> list:
        with DDGS() as ddgs:
            return list(ddgs.text(
                query,
                max_results=max_results,
                timelimit=timelimit,
            ))

    try:
        loop = asyncio.get_running_loop()
        raw_results = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_search),
            timeout=10,
        )
    except asyncio.TimeoutError as e:
        raise RuntimeError(
            f"{provider_label} search timed out"
        ) from e
    except Exception as e:
        raise RuntimeError(f"{provider_label} search failed: {e}") from e

    results: List[Dict[str, str]] = []
    if not raw_results:
        logger.info("DuckDuckGo returned 0 results for query: %s", query)
    for item in raw_results[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("href", ""),
            "snippet": item.get("body", ""),
        })
    return results


async def web_search(
    query: str,
    max_results: int = 5,
    time_range: Optional[str] = None,
) -> Dict[str, Any]:
    """Search the web using the best available provider.

    Tries SearXNG first (if SEARXNG_URL is set), then falls back to
    DuckDuckGo.

    Args:
        query: Search query string.
        max_results: Maximum number of results (1-20, default 5).
        time_range: Optional time filter (day, week, month, year).

    Returns:
        Dict with keys: results (list), provider (str), query (str).

    Raises:
        RuntimeError: If all search providers fail.
    """
    max_results = max(1, min(20, max_results))

    errors: List[str] = []

    # Try SearXNG first if configured
    if os.environ.get("SEARXNG_URL"):
        try:
            results = await _search_searxng(query, max_results, time_range)
            return {
                "results": results,
                "provider": "searxng",
                "query": query,
            }
        except RuntimeError as e:
            logger.warning("SearXNG search failed, falling back: %s", e)
            errors.append(f"SearXNG: {e}")

    # Fall back to DuckDuckGo
    try:
        results = await _search_duckduckgo(query, max_results, time_range)
        return {
            "results": results,
            "provider": "duckduckgo",
            "query": query,
        }
    except RuntimeError as e:
        errors.append(f"DuckDuckGo: {e}")

    raise RuntimeError(
        "All search providers failed: " + "; ".join(errors)
    )
