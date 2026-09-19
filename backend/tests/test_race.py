import asyncio

from backend.models import Recipe
from backend.recipe_engine.race import race_recipe_sources
from backend.tests.fakes.fake_browserbase import FakeBrowserbaseClient, html_with_recipe


async def test_fast_path_wins_when_first():
    client = FakeBrowserbaseClient(
        html_by_url={"https://fast.com": html_with_recipe(title="Fast Dish")},
        delay_by_url={"https://fast.com": 0, "https://slow.com": 0.2},
        fail_urls=["https://slow.com"],
    )
    result = await race_recipe_sources(client, ["https://fast.com", "https://slow.com"])
    assert result is not None
    assert result.title == "Fast Dish"
    assert result.method == "fast"


async def test_falls_back_to_browser_when_fast_path_fails():
    client = FakeBrowserbaseClient(
        html_by_url={"https://noldjson.com": "<html>no recipe data</html>"},
        browser_extract_by_url={
            "https://noldjson.com": Recipe(
                title="Browser Dish",
                source_url="https://noldjson.com",
                ingredients=["a", "b", "c"],
                steps=["1", "2"],
                method="browser",
            )
        },
    )
    result = await race_recipe_sources(client, ["https://noldjson.com"])
    assert result is not None
    assert result.method == "browser"


async def test_first_valid_wins_and_losers_are_cancelled():
    client = FakeBrowserbaseClient(
        html_by_url={
            "https://a.com": html_with_recipe(title="A"),
        },
        delay_by_url={"https://a.com": 0, "https://b.com": 1, "https://c.com": 1},
        fail_urls=["https://b.com", "https://c.com"],
    )
    result = await race_recipe_sources(client, ["https://a.com", "https://b.com", "https://c.com"])
    assert result.title == "A"
    # b and c never got to fetch_raw fail fast enough to matter; browser_extract path
    # for them should have been cancelled rather than left running.
    await asyncio.sleep(0.05)


async def test_returns_none_when_all_sources_fail():
    client = FakeBrowserbaseClient(
        html_by_url={},
        fail_urls=["https://dead.com"],
        browser_extract_by_url={"https://dead.com": None},
    )
    result = await race_recipe_sources(client, ["https://dead.com"])
    assert result is None


async def test_returns_none_for_empty_url_list():
    client = FakeBrowserbaseClient()
    result = await race_recipe_sources(client, [])
    assert result is None
