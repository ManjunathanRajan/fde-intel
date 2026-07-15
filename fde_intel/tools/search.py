"""Web search tool — Tavily (primary) with DuckDuckGo fallback when no API key set."""
from __future__ import annotations
import httpx
from fde_intel.config import TAVILY_API_KEY, MAX_SEARCH_RESULTS, REQUEST_TIMEOUT


async def _search_tavily(query: str, max_results: int) -> list[dict]:
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

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:800],
        }
        for r in data.get("results", [])
    ]


async def _search_duckduckgo(query: str, max_results: int) -> list[dict]:
    """DuckDuckGo instant answer API — no key required, best-effort fallback."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []

    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", query),
            "url": data.get("AbstractURL", ""),
            "content": data["AbstractText"][:800],
        })

    for topic in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(topic, dict) and topic.get("Text"):
            results.append({
                "title": topic.get("Text", "")[:60],
                "url": topic.get("FirstURL", ""),
                "content": topic.get("Text", "")[:800],
            })

    return results[:max_results]


async def search_web(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[dict]:
    """Search the web. Uses Tavily if API key set, falls back to DuckDuckGo."""
    if TAVILY_API_KEY:
        return await _search_tavily(query, max_results)
    return await _search_duckduckgo(query, max_results)
