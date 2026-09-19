from backend.recipe_engine.browserbase_client import BrowserbaseClient


def test_search_unwraps_duckduckgo_redirects_and_deduplicates():
    html = '''<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Frecipes.example%2Fsandwich">Recipe</a>
    <a class="result__a" href="https://recipes.example/sandwich">Duplicate</a>
    <a class="result__a" href="/l/?uddg=https%3A%2F%2Frecipes.example%2Fwrap">Wrap</a>
    <a class="result__a" href="javascript:alert(1)">Bad</a>'''
    assert BrowserbaseClient._extract_result_links(html, 3) == ['https://recipes.example/sandwich', 'https://recipes.example/wrap']
