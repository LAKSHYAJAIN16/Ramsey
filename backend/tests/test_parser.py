from backend.recipe_engine.parser import parse_recipe_from_html
from backend.tests.fakes.fake_browserbase import html_with_recipe


def test_parses_valid_json_ld_recipe():
    html = html_with_recipe(title="Shakshuka", ingredients=["1 onion", "6 eggs", "1 can tomatoes"], steps=["Saute onion.", "Add tomatoes.", "Crack in eggs."])
    recipe = parse_recipe_from_html(html, "https://example.com/shakshuka")

    assert recipe is not None
    assert recipe.title == "Shakshuka"
    assert recipe.servings == 4
    assert len(recipe.ingredients) == 3
    assert len(recipe.steps) == 3
    assert recipe.method == "fast"


def test_rejects_junk_extraction_with_too_few_ingredients():
    html = html_with_recipe(ingredients=["1 egg"], steps=["Cook it.", "Eat it."])
    recipe = parse_recipe_from_html(html, "https://example.com/junk")
    assert recipe is None


def test_rejects_junk_extraction_with_too_few_steps():
    html = html_with_recipe(ingredients=["1 egg", "1 cup flour", "1 cup milk"], steps=["Cook it."])
    recipe = parse_recipe_from_html(html, "https://example.com/junk")
    assert recipe is None


def test_returns_none_when_no_ld_json_present():
    recipe = parse_recipe_from_html("<html><body>nothing here</body></html>", "https://example.com/blank")
    assert recipe is None


def test_handles_string_instructions():
    import json

    ld = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Simple Toast",
        "recipeIngredient": ["bread", "butter", "salt"],
        "recipeInstructions": "Toast the bread.\nSpread butter.\nSprinkle salt.",
    }
    html = f'<html><script type="application/ld+json">{json.dumps(ld)}</script></html>'
    recipe = parse_recipe_from_html(html, "https://example.com/toast")
    assert recipe is not None
    assert len(recipe.steps) == 3


def test_handles_at_graph_wrapper():
    import json

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": "irrelevant"},
            {
                "@type": "Recipe",
                "name": "Graph Recipe",
                "recipeIngredient": ["a", "b", "c"],
                "recipeInstructions": [{"@type": "HowToStep", "text": "step one"}, {"@type": "HowToStep", "text": "step two"}],
            },
        ],
    }
    html = f'<html><script type="application/ld+json">{json.dumps(ld)}</script></html>'
    recipe = parse_recipe_from_html(html, "https://example.com/graph")
    assert recipe is not None
    assert recipe.title == "Graph Recipe"
