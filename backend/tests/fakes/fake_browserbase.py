"""Fakes shaped like BrowserbaseClient, for testing the race/parser/cache
logic without hitting a live API.
"""
import asyncio
from typing import Dict, List, Optional

from backend.models import Recipe


class FakeBrowserbaseClient:
    def __init__(
        self,
        search_results: Optional[List[str]] = None,
        html_by_url: Optional[Dict[str, str]] = None,
        delay_by_url: Optional[Dict[str, float]] = None,
        browser_extract_by_url: Optional[Dict[str, Optional[Recipe]]] = None,
        fail_urls: Optional[List[str]] = None,
    ):
        self.search_results = search_results or []
        self.html_by_url = html_by_url or {}
        self.delay_by_url = delay_by_url or {}
        self.browser_extract_by_url = browser_extract_by_url or {}
        self.fail_urls = fail_urls or []
        self.closed_urls: List[str] = []
        self.cancelled_urls: List[str] = []

    async def search(self, dish_name: str, limit: int = 3) -> List[str]:
        return self.search_results[:limit]

    async def fetch_raw(self, url: str) -> str:
        await asyncio.sleep(self.delay_by_url.get(url, 0))
        if url in self.fail_urls:
            raise RuntimeError(f"fetch failed for {url}")
        return self.html_by_url.get(url, "<html></html>")

    async def browser_extract(self, url: str) -> Optional[Recipe]:
        try:
            await asyncio.sleep(self.delay_by_url.get(url, 0) + 0.05)
            return self.browser_extract_by_url.get(url)
        except asyncio.CancelledError:
            self.cancelled_urls.append(url)
            raise
        finally:
            self.closed_urls.append(url)


def html_with_recipe(title="Test Dish", ingredients=None, steps=None) -> str:
    import json

    ingredients = ingredients or ["1 cup flour", "2 eggs", "1 cup milk"]
    steps = steps or ["Mix everything.", "Cook it.", "Serve."]
    ld_json = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": title,
        "recipeIngredient": ingredients,
        "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in steps],
        "recipeYield": "4 servings",
    }
    return f"<html><head><script type=\"application/ld+json\">{json.dumps(ld_json)}</script></head></html>"
