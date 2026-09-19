"""Race up to three candidate sources; first valid recipe wins.

Each source tries the fast path (fetch + deterministic parse) first and
falls back to a real browser (Stagehand) only if that fails. Whichever
source produces a valid recipe first wins; the rest are cancelled, which
also closes any browser sessions they had open (via their `finally`
blocks).
"""
import asyncio
from typing import List, Optional, Protocol

from backend.models import Recipe
from backend.recipe_engine.browserbase_client import fetch_and_parse_fast


class SourceClient(Protocol):
    async def fetch_raw(self, url: str) -> str: ...
    async def browser_extract(self, url: str) -> Optional[Recipe]: ...


async def resolve_source(client: SourceClient, url: str) -> Optional[Recipe]:
    try:
        recipe = await fetch_and_parse_fast(client, url)
        if recipe is not None:
            return recipe
    except Exception:
        pass

    try:
        return await client.browser_extract(url)
    except Exception:
        return None


async def race_recipe_sources(client: SourceClient, urls: List[str]) -> Optional[Recipe]:
    if not urls:
        return None

    tasks = [asyncio.ensure_future(resolve_source(client, url)) for url in urls]
    pending = set(tasks)
    winner: Optional[Recipe] = None

    while pending and winner is None:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                result = task.result()
            except Exception:
                result = None
            if result is not None:
                winner = result
                break

    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    return winner
