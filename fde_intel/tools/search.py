"""Web search tool wrapping Tavily API."""
from __future__ import annotations
import httpx
from fde_intel.config import TAVILY_API_KEY, MAX_SEARCH_RESULTS, REQUEST_TIMEOUT


async def search_web(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[dict]:
    """Return a list of {title, url, content} dicts for a search query."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for r in data.get("results", []):
        results.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:800],
            }
        )
    return results
