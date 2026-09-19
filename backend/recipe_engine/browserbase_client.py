"""Thin adapters over Browserbase + Stagehand.

These are the two integration points flagged as "known unknowns" in the
project brief (fetch(format="raw") returning real HTML, Stagehand.create
working off just the Browserbase key). Nothing here has been run against
the live API yet — verify against a real key before the demo (Tier 0).

Everything is written against a small interface (`search`, `fetch_raw`,
`browser_extract`) so `race.py` and the tests can swap in fakes without
caring whether the real SDK call shape below turns out to be right.
"""
from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote_plus

import httpx

from backend.models import Recipe
from backend.recipe_engine.parser import parse_recipe_from_html

SEARCH_ENGINE_URL = "https://html.duckduckgo.com/html/?q={query}"


class BrowserbaseClient:
    """Real implementation. Construct with an API key + project id.

    NOTE: `fetch_raw` and `browser_extract` call out to the Browserbase /
    Stagehand SDKs lazily (imported inside the method) so this module can
    be imported, and unit-tested via the fakes, without those packages
    installed.
    """

    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id

    async def search(self, dish_name: str, limit: int = 3) -> List[str]:
        """Return candidate recipe page URLs for a dish.

        Browserbase itself doesn't publish a dedicated "search" endpoint
        in the version this was written against, so this asks a
        JS-free search engine for results via a plain HTTP GET (cheap,
        no browser session needed) and pulls out result links. Swap this
        for a real Browserbase Search primitive if/when confirmed.
        """
        query = quote_plus(f"{dish_name} recipe")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(SEARCH_ENGINE_URL.format(query=query), headers={
                "User-Agent": "Mozilla/5.0 (Ramsey recipe search)",
            })
        resp.raise_for_status()
        return self._extract_result_links(resp.text, limit)

    @staticmethod
    def _extract_result_links(html: str, limit: int) -> List[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and href.startswith("http"):
                links.append(href)
            if len(links) >= limit:
                break
        return links

    async def fetch_raw(self, url: str) -> str:
        """Fetch a page's raw HTML through Browserbase's Fetch API.

        UNVERIFIED (Tier 0 item): confirm `format="raw"` actually returns
        rendered/static HTML for real recipe sites once a key is live.
        """
        from browserbase import Browserbase  # type: ignore

        bb = Browserbase(api_key=self.api_key)
        return await bb.fetch(url, project_id=self.project_id, format="raw")

    async def browser_extract(self, url: str) -> Optional[Recipe]:
        """Slow path: open a real cloud browser, close popups, read the DOM.

        UNVERIFIED (Tier 0 item): confirm Stagehand.create works with only
        the Browserbase key (Model Gateway), and that this live-view
        session shows up in the launcher's iframe.
        """
        from stagehand import Stagehand  # type: ignore

        stagehand = await Stagehand.create(browserbase_api_key=self.api_key)
        try:
            page = await stagehand.page.goto(url)
            await stagehand.page.act("close any popup, cookie banner, or newsletter modal")
            data = await stagehand.page.extract(
                "the recipe title, servings, ingredient list, and numbered steps"
            )
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
            await stagehand.close()


async def fetch_and_parse_fast(client: "BrowserbaseClient | object", url: str) -> Optional[Recipe]:
    """Fast path: fetch raw HTML, then deterministic JSON-LD parsing."""
    html = await client.fetch_raw(url)
    return parse_recipe_from_html(html, url)
