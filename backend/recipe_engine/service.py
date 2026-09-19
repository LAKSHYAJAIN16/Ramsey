from typing import Optional

from backend.models import Recipe
from backend.recipe_engine.cache import RecipeCache, load_demo_recipe
from backend.recipe_engine.race import SourceClient, race_recipe_sources

_cache = RecipeCache()


class RecipeNotFound(Exception):
    pass


async def get_recipe(client: SourceClient, dish_name: str, use_cache: bool = True) -> Recipe:
    """Return an actual recipe or an explicit failure; never substitute another dish."""
    if use_cache:
        cached = _cache.get(dish_name)
        if cached is not None:
            return cached

    urls = await client.search(dish_name, limit=3)
    recipe = await race_recipe_sources(client, urls)

    if recipe is None:
        raise RecipeNotFound("No usable recipe found. Try a more specific dish name; the demo is available separately.")
    else:
        _cache.set(dish_name, recipe)

    return recipe


def cache_size() -> int:
    return len(_cache)
