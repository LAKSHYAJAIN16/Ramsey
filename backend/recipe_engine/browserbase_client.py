"""Real adapters over Browserbase Fetch and Stagehand.

Browserbase Fetch — verified against docs.browserbase.com/platform/fetch
(Sept 2026):
    POST https://api.browserbase.com/v1/fetch
    header: X-BB-API-Key
    body:   {"url": ..., "format": "raw" | "markdown" | "json", ...}
    "raw" is the default and returns the unmodified upstream response
    body in the `content` field - this resolves the brief's "known
    unknown" #1: yes, fetch(format="raw") returns real page HTML.

Browserbase doesn't expose a dedicated web-search endpoint, so `search`
below asks a JS-free search engine for results *through Browserbase
Fetch* (not a raw httpx call) and pulls out result links - it still runs
everything through Browserbase, it just treats the search results page
as another URL to fetch.

Stagehand — verified against docs.stagehand.dev/v3/sdk/python and the
stagehand PyPI quickstart (Sept 2026):
    pip install stagehand
    from stagehand import AsyncStagehand
    client = AsyncStagehand(browserbase_api_key=...)      # Model Gateway:
                                                           # no separate
                                                           # model provider
                                                           # key needed
    session = await client.sessions.start(model_name="...")
    await session.navigate(url=...)
    await session.act(input="...")
    await session.extract(instruction="...", schema={...})
    await session.end()
This resolves "known unknown" #2 (Stagehand works off just the
Browserbase key via Model Gateway). Still unverified live: whether
`.sessions.start` or `.sessions.create` is the current method name -
docs mirrors disagreed on this, so it's worth a quick smoke test before
the demo (Tier 0).
"""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs

import httpx

from backend.models import Recipe
from backend.recipe_engine.parser import parse_recipe_from_html

BROWSERBASE_FETCH_URL = "https://api.browserbase.com/v1/fetch"
SEARCH_ENGINE_URL = "https://html.duckduckgo.com/html/?q={query}"


class BrowserbaseClient:
    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id

    async def fetch_raw(self, url: str, format: str = "raw") -> str:
        """POST /v1/fetch. Returns the `content` field (page HTML for
        format="raw")."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BROWSERBASE_FETCH_URL,
                headers={"X-BB-API-Key": self.api_key, "Content-Type": "application/json"},
                json={"url": url, "format": format},
            )
        resp.raise_for_status()
        data = resp.json()
        return data.get("content", "")

    async def search(self, dish_name: str, limit: int = 3) -> List[str]:
        """Candidate recipe page URLs for a dish, fetched through
        Browserbase (not a direct httpx call to the search engine)."""
        query = quote_plus(f"{dish_name} recipe")
        html = await self.fetch_raw(SEARCH_ENGINE_URL.format(query=query))
        return self._extract_result_links(html, limit)

    @staticmethod
    def _extract_result_links(html: str, limit: int) -> List[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        for a in soup.select("a.result__a"):
            href = urljoin("https://duckduckgo.com", a.get("href") or "")
            parsed = urlparse(href)
            if parsed.hostname in {"duckduckgo.com", "www.duckduckgo.com"}:
                href = parse_qs(parsed.query).get("uddg", [""])[0]
            if urlparse(href).scheme in {"http", "https"} and href not in links:
                links.append(href)
            if len(links) >= limit:
                break
        return links

    async def browser_extract(self, url: str) -> Optional[Recipe]:
        """Slow path: open a real cloud browser, close popups, read the DOM."""
        from stagehand import AsyncStagehand  # type: ignore

        client = AsyncStagehand(browserbase_api_key=self.api_key)
        session = await client.sessions.start(model_name="anthropic/claude-sonnet-4-6")
        try:
            await session.navigate(url=url)
            await session.act(input="close any popup, cookie banner, or newsletter modal")
            extraction = await session.extract(
                instruction="the recipe title, servings, ingredient list, and numbered steps",
                schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "servings": {"type": "integer"},
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "steps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["ingredients", "steps"],
                },
            )
            data = extraction.data if hasattr(extraction, "data") else extraction
            ingredients = data.get("ingredients", [])
            steps = data.get("steps", [])
            if len(ingredients) < 3 or len(steps) < 2:
                return None
            return Recipe(
                title=data.get("title", "Untitled recipe"),
                source_url=url,
                servings=data.get("servings"),
                ingredients=ingredients,
                steps=steps,
                method="browser",
            )
        finally:
            await session.end()


async def fetch_and_parse_fast(client: "BrowserbaseClient | object", url: str) -> Optional[Recipe]:
    """Fast path: fetch raw HTML, then deterministic JSON-LD parsing."""
    html = await client.fetch_raw(url)
    return parse_recipe_from_html(html, url)
