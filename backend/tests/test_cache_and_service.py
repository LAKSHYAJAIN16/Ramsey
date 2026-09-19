from backend.recipe_engine.cache import RecipeCache, load_demo_recipe
from backend.recipe_engine.service import get_recipe
from backend.tests.fakes.fake_browserbase import FakeBrowserbaseClient, html_with_recipe


def test_demo_recipe_loads_and_is_valid():
    recipe = load_demo_recipe()
    assert recipe.title
    assert len(recipe.ingredients) >= 3
    assert len(recipe.steps) >= 2
    assert recipe.method == "demo"


def test_cache_roundtrip():
    cache = RecipeCache()
    recipe = load_demo_recipe()
    assert cache.get("shakshuka") is None
    cache.set("Shakshuka", recipe)
    assert cache.get("shakshuka") is recipe  # case-insensitive


async def test_service_falls_back_to_demo_when_nothing_resolves():
    client = FakeBrowserbaseClient(search_results=["https://dead.com"], fail_urls=["https://dead.com"], browser_extract_by_url={"https://dead.com": None})
    recipe = await get_recipe(client, "nonexistent dish 12345", use_cache=False)
    assert recipe.method == "demo"


async def test_service_returns_real_recipe_when_found():
    client = FakeBrowserbaseClient(
        search_results=["https://good.com"],
        html_by_url={"https://good.com": html_with_recipe(title="Real Dish")},
    )
    recipe = await get_recipe(client, "real dish", use_cache=False)
    assert recipe.title == "Real Dish"
